
from mcp_server.central_server import mcp
from pathlib import Path
import pdfplumber
import docx

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
SUPPORTED_FORMATS = [".pdf", ".txt", ".md", ".docx"]

def _extract_text(file_path: Path) -> str:
    """Internal Helper - When necessary, extract text from the file depending
    on the type of extension"""

    ext = file_path.suffix.lower()

    if ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
        )
    
    elif ext == ".docx":
        doc = docx.Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)
    elif ext in (".md", ".txt"):
        return file_path.read_text(encoding="utf-8")
    return f"Unsupported file type: {ext}"

@mcp.tool()
def read_resume() -> str:
    """ Read the User's Resume/Profile from the assigned Workspace,
    You have to use this tool when you want to understand User's Skills, 
    experience, projects and strengths to give a personalized Response"""

    resume_path = WORKSPACE_ROOT/"workspace_profile"

    if not resume_path.exists():
        return "Error: folder does not exist"
    
    for fmt in SUPPORTED_FORMATS:
        matches = list(resume_path.glob(f"*{fmt}"))
        if matches:
            found_file = matches[0]
            content = _extract_text(found_file)

            return f"[Source: {found_file.name}]\n\n{content}"

    return ("No resume found in workspace_profile/. "
            "Please add a resume.pdf, resume.docx,resume.md, or resume.txt file there.")

