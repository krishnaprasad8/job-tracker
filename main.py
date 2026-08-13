from fastapi import FastAPI

app = FastAPI()

@app.get("/applications")
def list_applications():
    return [{"company": "Test Co", "status": "applied"}]
