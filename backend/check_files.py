from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import PDFFile

# 创建数据库连接
engine = create_engine('sqlite:////Users/jiaxinming/JxmWork/walmart-a/backend/data/walmart_pdf_parser.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# 查询所有PDF文件
print("已导入的PDF文件:")
print("ID | 文件名 | 文件哈希")
print("-" * 50)

files = db.query(PDFFile).all()
for f in files:
    print(f"{f.id} | {f.filename} | {f.file_hash}")

print(f"\n总计: {len(files)}个文件")

db.close()
