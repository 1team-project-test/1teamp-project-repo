import os
import json
import glob
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

def build_rag_index(root_folder=r"C:\data"):
    print("1. 한국어 최적화 임베딩 모델 로딩 중... (최초 1회 다운로드 소요)")
    # 한국어 문맥을 아주 잘 이해하는 가벼운 모델입니다.
    embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")
    
    print("2. 로컬 벡터 DB(ChromaDB) 준비 중...")
    # 프로젝트 폴더 내에 chroma_db라는 폴더로 데이터베이스를 구성합니다.
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings,
        collection_name="interview_expert_data"
    )
    
    print(f"3. {root_folder} 경로의 JSON 파일 탐색 중...")
    # C:\data 하위의 모든 json 파일을 찾습니다.
    json_files = glob.glob(os.path.join(root_folder, "**/*.json"), recursive=True)
    print(f"총 {len(json_files)}개의 면접 데이터를 발견했습니다. 인덱싱 시작!\n")
    
    docs_batch = []
    batch_size = 500  # 💡 데이터가 너무 커서 컴퓨터가 멈추는 것을 방지! 500개씩 나눠서 안전하게 저장합니다.
    
    for i, file_path in enumerate(json_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 아까 확인했던 AI-Hub JSON 구조에서 핵심 알맹이만 쏙 빼냅니다.
                q = data["dataSet"]["question"]["raw"]["text"]
                a = data["dataSet"]["answer"]["raw"]["text"]
                job = data["dataSet"]["info"]["occupation"]
                
                # AI가 나중에 검색하기 좋게 하나의 문단으로 포장
                text = f"직무: {job}\n질문: {q}\n모범답변: {a}"
                
                # 메타데이터(직무)를 꼬리표로 달아서 박스에 담습니다.
                docs_batch.append(Document(page_content=text, metadata={"job": job, "source": file_path}))
                
                # 500개가 모이면 DB에 밀어 넣고 박스를 싹 비웁니다.
                if len(docs_batch) >= batch_size:
                    vectorstore.add_documents(docs_batch)
                    print(f"✅ 진행 상황: {i+1}개 파일 적재 완료...")
                    docs_batch = [] # 메모리 초기화
                    
        except Exception as e:
            # 혹시 AI-Hub 데이터 중 형식이 어긋난 불량 파일이 있으면 조용히 건너뜁니다.
            continue
    
    # 500개 단위로 넣고 남은 자투리 데이터 마저 저장
    if docs_batch:
        vectorstore.add_documents(docs_batch)
        
    print(f"\n🎉 총 {len(json_files)}개 데이터 인덱싱 완벽 종료!")
    print("프로젝트 폴더를 확인해 보세요. 'chroma_db'라는 지식 창고 폴더가 생성되었습니다.")

# 이 파이썬 파일을 직접 실행했을 때만 작동하도록 보호
if __name__ == "__main__":
    build_rag_index()