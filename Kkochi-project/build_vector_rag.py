# build_vector_rag.py (멀티프로세싱 및 배치 공법을 적용한 초고속 RAG 벡터 빌더)
import os
import json
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm 
from multiprocessing import Pool, cpu_count # 💡 멀티코어 병렬 처리를 위한 파이썬 표준 라이브러리

def parse_single_json(file_info):
    """📂 [병렬 워커] CPU 코어들이 각자 파일 주소를 들고 가서 독립적으로 초고속 파싱 연산"""
    file_path, filename = file_info
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        dataset = data.get("dataSet", {})
        q_raw = dataset.get("question", {}).get("raw", {})
        a_raw = dataset.get("answer", {}).get("raw", {})
        info = dataset.get("info", {})
        
        q_text = q_raw.get("text", "").strip()
        a_text = a_raw.get("text", "").strip()
        occupation = info.get("occupation", "공통")
        
        if q_text and a_text:
            combined_text = f"직군분야: {occupation} \n면접관 기출질문: {q_text} \n합격자 실제답변: {a_text}"
            return {
                "document": combined_text,
                "metadata": {"filename": filename, "occupation": occupation}
            }
    except:
        pass
    return None

def build_interview_vector_database():
    print("\n" + "="*60)
    print("🚀 [KKOCHI-RAG SPEED MASTER] 초고속 멀티프로세싱 엠베딩 가동")
    print("="*60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    base_data_dirs = [
        os.path.join(project_root, "data", "Training"),
        os.path.join(project_root, "data", "Validation")
    ]
    
    chroma_path = os.path.join(project_root, "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    
    print("🧠 1/4 단계: 허깅페이스 정식 인공지능 모델(multilingual-e5-base) 로드 중...")
    korean_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="intfloat/multilingual-e5-base"
    )
    
    collection = client.get_or_create_collection(
        name="kkochi_ai_rag", 
        embedding_function=korean_embedding_fn
    )
    
    print("📂 2/4 단계: data/ 내부 하위 직군별 폴더 트리 구조 정밀 스캔 시작...")
    json_files_pool = []
    for target_dir in base_data_dirs:
        if not os.path.exists(target_dir):
            continue
        for root, dirs, files in os.walk(target_dir):
            for filename in files:
                if filename.endswith(".json"):
                    json_files_pool.append((os.path.join(root, filename), filename))
                    
    total_files = len(json_files_pool)
    print(f"🎯 스캔 완료: 총 {total_files}개의 JSON 파일 발견.")
    print("-" * 60)
    
    # 💡 [속도 대폭발의 핵심 1] 내 컴퓨터가 가진 실제 CPU 스레드/코어 개수(예: 8, 12, 16)를 100% 한도까지 풀가동!
    cores = cpu_count()
    print(f"🔥 3/4 단계: 총 {cores}개의 CPU 멀티코어 풀가동, 고속 병렬 파싱 시작...")
    
    parsed_results = []
    # 멀티프로세싱 풀을 생성하여 파일을 병렬로 분할 덤프 처리
    with Pool(processes=cores) as pool:
        parsed_results = list(tqdm(
            pool.imap(parse_single_json, json_files_pool, chunksize=50), 
            total=total_files, 
            desc="CPU 병렬 파싱 진행률"
        ))
        
    print("-" * 60)
    print("🚢 4/4 단계: 파싱 완료된 텍스트 뭉치들을 ChromaDB에 대량 배치(Batch) 적재 개시...")
    
    # 깨끗한 데이터만 추려내기
    valid_data = [r for r in parsed_results if r is not None]
    
    # 💡 [속도 대폭발의 핵심 2] 1개씩 노크하던 방식을 버리고 100개씩 한 바구니에 묶어서 번개처럼 인서트!
    batch_size = 100
    inserted_count = 0
    
    with tqdm(total=len(valid_data), desc="ChromaDB 벡터 보관함 안착 중", unit="batch") as pbar:
        for i in range(0, len(valid_data), batch_size):
            chunk = valid_data[i:i+batch_size]
            
            docs = [item["document"] for item in chunk]
            metas = [item["metadata"] for item in chunk]
            ids = [f"rag_{inserted_count + idx + 1}" for idx in range(len(chunk))]
            
            # 뭉텅이로 대량 주입 가동
            collection.add(documents=docs, metadatas=metas, ids=ids)
            inserted_count += len(chunk)
            pbar.update(len(chunk))
                
    print("="*60)
    print(f"✨ [Vector RAG 고속 빌딩 전면 완료!]")
    print(f"📁 저장소 폴더 경로: {chroma_path}")
    print(f"📊 최종 고속 수송 통계: 총 {inserted_count}개의 기출 족보가 초고속 적재 완료되었습니다!")
    print("="*60 + "\n")

if __name__ == "__main__":
    build_interview_vector_database()
