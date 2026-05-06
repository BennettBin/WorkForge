from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.entities import FileRecord, OutputFile, Task
from app.services.repository_factory import build_repository_bundle


def test_json_repository_create_query_update_and_version():
    with TemporaryDirectory() as temp_dir:
        repos = build_repository_bundle(Path(temp_dir))

        task = Task(task_id="t-1", user_id="u-1", user_requirement="generate slides")
        repos.tasks.create(task)
        fetched = repos.tasks.get_by_id("t-1")
        assert fetched is not None
        assert fetched.task_id == "t-1"

        updated = repos.tasks.update_status("t-1", "planning")
        assert updated is not None
        assert updated.status == "planning"

        file_record = FileRecord(
            file_id="f-1",
            task_id="t-1",
            file_name="paper.pdf",
            file_type="pdf",
            file_path="/tmp/paper.pdf",
            file_size_bytes=1024,
        )
        repos.files.create(file_record)
        files = repos.files.list_by_task("t-1")
        assert len(files) == 1

        output_v1 = OutputFile(output_id="o-1", task_id="t-1", version=1, file_path="/tmp/output-v1.pptx")
        repos.outputs.create(output_v1)
        output_v2 = OutputFile(output_id="o-2", task_id="t-1", version=2, file_path="/tmp/output-v2.pptx")
        repos.outputs.create(output_v2)

        latest = repos.outputs.get_latest("t-1")
        assert latest is not None
        assert latest.version == 2
