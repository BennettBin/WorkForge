import json
from pathlib import Path
from typing import Any, Optional

from pptx import Presentation
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.util import Inches, Pt


class PptxExportError(Exception):
    pass


class PptxExporter:
    def export(
        self,
        slides: list[dict[str, Any]],
        output_path: Path,
        template_path: Optional[Path] = None,
        template_bundle: Optional[dict[str, Any]] = None,
    ) -> Path:
        try:
            effective_template_path = template_path
            if template_bundle and template_bundle.get("template_file"):
                effective_template_path = Path(str(template_bundle["template_file"]))
            meta, rules = self._load_bundle_meta_rules(template_bundle)
            text_rule = self._resolve_text_overflow_rule(rules)
            title_size_pt, body_size_pt = self._resolve_text_sizes(meta)

            if effective_template_path is not None and effective_template_path.exists():
                prs = Presentation(str(effective_template_path))
                self._clear_existing_slides(prs)
            else:
                prs = Presentation()
            title_layout = self._pick_layout(prs, (meta.get("layout_map") or {}).get("cover"), fallback=0)
            content_layout = self._pick_layout(prs, (meta.get("layout_map") or {}).get("content"), fallback=1 if len(prs.slide_layouts) > 1 else 0)
            blank_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]

            for index, slide in enumerate(slides):
                kind = slide.get("kind", "content")
                image_placeholders = slide.get("image_placeholders", []) or []
                if index == 0 or kind == "cover":
                    s = prs.slides.add_slide(title_layout)
                    if s.shapes.title is not None:
                        s.shapes.title.text = self._apply_text_rule(str(slide.get("title", "Cover")), text_rule, 120)
                        self._apply_shape_font_size(s.shapes.title, title_size_pt)
                    subtitle = s.placeholders[1] if len(s.placeholders) > 1 else None
                    if subtitle is not None:
                        subtitle.text = "\n".join(
                            [self._apply_text_rule(str(x), text_rule, 120) for x in (slide.get("bullets", [])[:2])]
                        )
                        self._apply_shape_font_size(subtitle, body_size_pt)
                elif image_placeholders:
                    s = prs.slides.add_slide(blank_layout)
                    self._render_slide_with_image_placeholder(s, slide, title_size_pt=title_size_pt, body_size_pt=body_size_pt, text_rule=text_rule)
                else:
                    s = prs.slides.add_slide(content_layout)
                    if s.shapes.title is not None:
                        s.shapes.title.text = self._apply_text_rule(str(slide.get("title", f"Slide {index + 1}")), text_rule, 120)
                        self._apply_shape_font_size(s.shapes.title, title_size_pt)
                    body = None
                    for ph in s.placeholders:
                        if hasattr(ph, "text_frame") and ph.placeholder_format.idx != 0:
                            body = ph
                            break
                    if body is not None:
                        tf = body.text_frame
                        tf.clear()
                        bullets = slide.get("bullets", []) or ["TBD"]
                        for i, bullet in enumerate(bullets):
                            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                            p.text = self._apply_text_rule(str(bullet), text_rule, 220)
                            p.font.size = Pt(body_size_pt)

                if s.has_notes_slide:
                    s.notes_slide.notes_text_frame.text = self._apply_text_rule(str(slide.get("notes", "")), text_rule, 1200)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            prs.save(str(output_path))
            return output_path
        except Exception as exc:
            raise PptxExportError(f"PPTX export failed: {exc}") from exc

    def _pick_layout(self, prs: Presentation, preferred_name: Any, fallback: int):
        name = str(preferred_name or "").strip().lower()
        if name:
            for layout in prs.slide_layouts:
                if str(getattr(layout, "name", "") or "").strip().lower() == name:
                    return layout
        idx = max(0, min(fallback, len(prs.slide_layouts) - 1))
        return prs.slide_layouts[idx]

    def _load_bundle_meta_rules(self, template_bundle: Optional[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
        if not template_bundle:
            return {}, {}
        meta_path = Path(str(template_bundle.get("meta_path", ""))) if template_bundle.get("meta_path") else None
        rules_path = Path(str(template_bundle.get("rules_path", ""))) if template_bundle.get("rules_path") else None
        meta: dict[str, Any] = {}
        rules: dict[str, Any] = {}
        if meta_path and meta_path.exists():
            try:
                loaded = json.loads(meta_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    meta = loaded
            except Exception:
                meta = {}
        if rules_path and rules_path.exists():
            try:
                loaded = json.loads(rules_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    rules = loaded
            except Exception:
                rules = {}
        return meta, rules

    def _resolve_text_sizes(self, meta: dict[str, Any]) -> tuple[float, float]:
        text_style = meta.get("text_style") if isinstance(meta, dict) else {}
        title = text_style.get("title") if isinstance(text_style, dict) else {}
        body = text_style.get("body") if isinstance(text_style, dict) else {}
        try:
            title_size = float(title.get("size_pt")) if isinstance(title, dict) and title.get("size_pt") is not None else 30.0
        except Exception:
            title_size = 30.0
        try:
            body_size = float(body.get("size_pt")) if isinstance(body, dict) and body.get("size_pt") is not None else 18.0
        except Exception:
            body_size = 18.0
        return title_size, body_size

    def _resolve_text_overflow_rule(self, rules: dict[str, Any]) -> str:
        rows = rules.get("rules", []) if isinstance(rules, dict) else []
        if not isinstance(rows, list):
            return "truncate"
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("name", "")).strip().lower() == "text_overflow":
                action = str(row.get("action", "")).strip().lower()
                if action in {"truncate", "shrink"}:
                    return action
        return "truncate"

    def _apply_text_rule(self, text: str, rule: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        if rule == "truncate":
            return text[: max_len - 1].rstrip() + "…"
        # shrink: keep full text, rely on smaller font
        return text

    def _apply_shape_font_size(self, shape: Any, size_pt: float) -> None:
        if not hasattr(shape, "text_frame") or shape.text_frame is None:
            return
        for para in shape.text_frame.paragraphs:
            para.font.size = Pt(size_pt)

    def _clear_existing_slides(self, prs: Presentation) -> None:
        slide_id_list = prs.slides._sldIdLst
        slides = list(slide_id_list)
        for slide_id in slides:
            rel_id = slide_id.rId
            prs.part.drop_rel(rel_id)
            slide_id_list.remove(slide_id)

    def _render_slide_with_image_placeholder(
        self,
        slide_obj,
        slide_data: dict[str, Any],
        *,
        title_size_pt: float,
        body_size_pt: float,
        text_rule: str,
    ) -> None:
        # Title area
        title_box = slide_obj.shapes.add_textbox(Inches(0.6), Inches(0.3), Inches(12.0), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.text = self._apply_text_rule(str(slide_data.get("title", "Content")), text_rule, 120)
        tf_title.paragraphs[0].font.size = Pt(title_size_pt)

        # Left text content area
        left_box = slide_obj.shapes.add_textbox(Inches(0.7), Inches(1.4), Inches(6.1), Inches(5.2))
        tf_left = left_box.text_frame
        tf_left.clear()
        bullets = slide_data.get("bullets", []) or ["TBD"]
        for i, bullet in enumerate(bullets[:6]):
            p = tf_left.paragraphs[0] if i == 0 else tf_left.add_paragraph()
            p.text = self._apply_text_rule(str(bullet), text_rule, 200)
            p.level = 0
            p.font.size = Pt(body_size_pt)

        # Right image reserved area
        image_shape = slide_obj.shapes.add_shape(
            autoshape_type_id=MSO_AUTO_SHAPE_TYPE.RECTANGLE,
            left=Inches(7.1),
            top=Inches(1.6),
            width=Inches(5.6),
            height=Inches(4.7),
        )
        image_shape.fill.background()
        image_shape.line.width = Pt(1.5)

        ph = (slide_data.get("image_placeholders") or [{}])[0]
        label = str(ph.get("label", "Image placeholder"))[:120]
        source = str(ph.get("source", "unknown"))[:200]
        info_box = slide_obj.shapes.add_textbox(Inches(7.3), Inches(1.9), Inches(5.2), Inches(4.2))
        tf_info = info_box.text_frame
        tf_info.clear()
        p0 = tf_info.paragraphs[0]
        p0.text = "IMAGE PLACEHOLDER"
        p0.font.size = Pt(16)
        p1 = tf_info.add_paragraph()
        p1.text = f"Label: {label}"
        p1.font.size = Pt(12)
        p2 = tf_info.add_paragraph()
        p2.text = f"Source: {source}"
        p2.font.size = Pt(11)
