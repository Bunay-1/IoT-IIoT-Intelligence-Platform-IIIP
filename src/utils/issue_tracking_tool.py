from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory storage for issues
issues = []


class Issue(BaseModel):
    id: int
    title: str
    description: str
    status: str
    assignee: Optional[str] = None


@app.get("/issues/", response_model=List[Issue])
def get_issues():
    """
    Retrieve all issues.
    Returns:
        List[Issue]: List of all issues.
    """
    return issues


@app.get("/issues/{issue_id}", response_model=Issue)
def get_issue(issue_id: int):
    """
    Retrieve a specific issue by ID.
    Args:
        issue_id (int): ID of the issue to retrieve.
    Returns:
        Issue: The requested issue.
    """
    for issue in issues:
        if issue.id == issue_id:
            return issue
    raise HTTPException(status_code=404, detail="Issue not found")


@app.post("/issues/", response_model=Issue)
def create_issue(issue: Issue):
    """
    Create a new issue.
    Args:
        issue (Issue): Issue data to create.
    Returns:
        Issue: The created issue.
    """
    issues.append(issue)
    return issue


@app.put("/issues/{issue_id}", response_model=Issue)
def update_issue(issue_id: int, updated_issue: Issue):
    """
    Update an existing issue.
    Args:
        issue_id (int): ID of the issue to update.
        updated_issue (Issue): Updated issue data.
    Returns:
        Issue: The updated issue.
    """
    for i, issue in enumerate(issues):
        if issue.id == issue_id:
            issues[i] = updated_issue
            return updated_issue
    raise HTTPException(status_code=404, detail="Issue not found")


@app.delete("/issues/{issue_id}", response_model=Issue)
def delete_issue(issue_id: int):
    """
    Delete an issue by ID.
    Args:
        issue_id (int): ID of the issue to delete.
    Returns:
        Issue: The deleted issue.
    """
    for i, issue in enumerate(issues):
        if issue.id == issue_id:
            deleted_issue = issues.pop(i)
            return deleted_issue
    raise HTTPException(status_code=404, detail="Issue not found")


def run():
    """
    Run the issue tracking tool.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
