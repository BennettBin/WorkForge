from pathlib import Path
from typing import Any, Optional

from pptx import Presentation
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.util import Inches, Pt


class PptxExportError(Exception):
    pass


class PptxExporter:
    def export(self, slides: list[dict[str, Any]], output_path: Path, template_path: Optional[Path] = None) -> Path:
        try:
            if template_path is not None and template_path.exists():
                prs = Presentation(str(template_path))
                self._clear_existing_slides(prs)
            else:
                prs = Presentation()
            title_layout = prs.slide_layouts[0]
            content_layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
            blank_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]

            for index, slide in enumerate(slides):
                kind = slide.get("kind", "content")
                image_placeholders = slide.get("image_placeholders", []) or []
                if index == 0 or kind == "cover":
                    s = prs.slides.add_slide(title_layout)
                    if s.shapes.title is not None:
                        s.shapes.title.text = slide.get("title", "Cover")
                    subtitle = s.placeholders[1] if len(s.placeholders) > 1 else None
                    if subtitle is not None:
                        subtitle.text = "\n".join(slide.get("bullets", [])[:2])
                elif image_placeholders:
                    s = prs.slides.add_slide(blank_layout)
                    self._render_slide_with_image_placeholder(s, slide)
                else:
                    s = prs.slides.add_slide(content_layout)
                    if s.shapes.title is not None:
                        s.shapes.title.text = slide.get("title", f"Slide {index + 1}")
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
                            p.text = bullet

                if s.has_notes_slide:
                    s.notes_slide.notes_text_frame.text = slide.get("notes", "")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            prs.save(str(output_path))
            return output_path
        except Exception as exc:
            raise PptxExportError(f"PPTX export failed: {exc}") from exc

    def _clear_existing_slides(self, prs: Presentation) -> None:
        slide_id_list = prs.slides._sldIdLst
        slides = list(slide_id_list)
        for slide_id in slides:
            rel_id = slide_id.rId
            prs.part.drop_rel(rel_id)
            slide_id_list.remove(slide_id)

    def _render_slide_with_image_placeholder(self, slide_obj, slide_data: dict[str, Any]) -> None:
        # Title area
        title_box = slide_obj.shapes.add_textbox(Inches(0.6), Inches(0.3), Inches(12.0), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.text = str(slide_data.get("title", "Content"))
        tf_title.paragraphs[0].font.size = Pt(30)

        # Left text content area
        left_box = slide_obj.shapes.add_textbox(Inches(0.7), Inches(1.4), Inches(6.1), Inches(5.2))
        tf_left = left_box.text_frame
        tf_left.clear()
        bullets = slide_data.get("bullets", []) or ["TBD"]
        for i, bullet in enumerate(bullets[:6]):
            p = tf_left.paragraphs[0] if i == 0 else tf_left.add_paragraph()
            p.text = str(bullet)
            p.level = 0
            p.font.size = Pt(18)

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
