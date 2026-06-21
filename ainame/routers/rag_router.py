import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends

from core.auth import AuthHandler

auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["企业知识库"])

# 启动项目所在的根文件的路径，在我们项目中是ai397下main创建一个文件夹uploads
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

from core.rag_service import process_and_stor_file
@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks,file: UploadFile = File(...), user_id: int = Depends(auth_handler.auth_access_dependency)):
    """
    用户上传专属参考文件（TXT/PDF）
    """
    # 第一步：完成文件在服务器的保存
    file_path =os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 第二步：把已经上传的文件，插入到知识库的数据库中
    background_tasks.add_task(process_and_stor_file,file_path,user_id)

    return {
        "result": "success",
        "message": f"文件 {file.filename} 上传成功！后台正在为您构建专属知识库，请稍候测试起名功能。"
    }
