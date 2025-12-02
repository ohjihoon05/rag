#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Local RAG Benchmark Test
Skald 블로그 방법론 참고: https://blog.yakkomajuri.com/blog/local-rag

Direct Retrieval API를 사용하여 검색 품질 테스트
- BM25 (keyword) vs Vector vs Hybrid 비교
- TopK 변화에 따른 품질 측정
"""

import time
import json
import requests
from datetime import datetime

# Configuration
API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://localhost"

# Test Questions - Skald 스타일 분류
TEST_QUESTIONS = [
    # Type 1: Point Query (단일 정보 조회)
    {
        "question": "한소희",
        "type": "point",
        "expected_in_chunks": ["한소희"],
        "description": "담당자 이름으로 검색"
    },
    {
        "question": "제품E 판매",
        "type": "point",
        "expected_in_chunks": ["제품E"],
        "description": "제품명으로 검색"
    },
    {
        "question": "서울 지역",
        "type": "point",
        "expected_in_chunks": ["서울"],
        "description": "지역명으로 검색"
    },
    # Type 2: Aggregation Query (집계 필요)
    {
        "question": "영업부 담당자들",
        "type": "aggregation",
        "expected_in_chunks": ["영업부"],
        "description": "부서별 데이터 집계"
    },
    {
        "question": "매출액이 높은 거래",
        "type": "aggregation",
        "expected_in_chunks": ["매출"],
        "description": "매출 관련 데이터"
    },
    # Type 3: Semantic Query (의미적 검색)
    {
        "question": "실적이 좋은 사람",
        "type": "semantic",
        "expected_in_chunks": ["매출", "판매"],
        "description": "의미적 유사성 테스트"
    },
    {
        "question": "가장 많이 팔린 상품",
        "type": "semantic",
        "expected_in_chunks": ["판매수량", "제품"],
        "description": "의미적 유사성 테스트"
    },
]

# Search configurations to test
SEARCH_CONFIGS = [
    {
        "name": "BM25 Only",
        "keywords_similarity_weight": 1.0,
        "top_k": 30,
        "description": "키워드 검색만 (전통적 방식)"
    },
    {
        "name": "Vector Only",
        "keywords_similarity_weight": 0.0,
        "top_k": 30,
        "description": "벡터 검색만 (의미적 검색)"
    },
    {
        "name": "Hybrid Balanced",
        "keywords_similarity_weight": 0.5,
        "top_k": 30,
        "description": "BM25 + Vector 균형"
    },
    {
        "name": "Hybrid Keyword Heavy",
        "keywords_similarity_weight": 0.7,
        "top_k": 30,
        "description": "키워드 가중치 높음"
    },
    {
        "name": "Hybrid High TopK",
        "keywords_similarity_weight": 0.5,
        "top_k": 100,
        "description": "Skald 스타일 높은 TopK"
    },
]


def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


def list_datasets():
    """Get list of existing datasets"""
    url = f"{BASE_URL}/api/v1/datasets"
    r = requests.get(url, headers=get_headers())
    data = r.json()
    if data.get("code") == 0:
        return data.get("data", [])
    return []


def retrieve_chunks(dataset_ids, question, top_k=30, similarity_threshold=0.2, keywords_similarity_weight=0.5):
    """Direct Retrieval API call with configurable parameters"""
    url = f"{BASE_URL}/api/v1/retrieval"
    payload = {
        "dataset_ids": dataset_ids,
        "question": question,
        "top_k": top_k,
        "similarity_threshold": similarity_threshold,
        "keywords_similarity_weight": keywords_similarity_weight
    }

    start_time = time.time()
    r = requests.post(url, headers=get_headers(), json=payload)
    elapsed = time.time() - start_time

    data = r.json()
    if data.get("code") == 0:
        chunks = data.get("data", {}).get("chunks", [])
        return chunks, elapsed
    return [], elapsed


def check_chunk_relevance(chunks, expected_keywords):
    """Check if retrieved chunks contain expected keywords"""
    if not chunks:
        return 0, 0, []

    total_chunks = len(chunks)
    relevant_chunks = 0
    matched_keywords = set()

    for chunk in chunks:
        content = chunk.get("content", "").lower()
        for kw in expected_keywords:
            if kw.lower() in content:
                relevant_chunks += 1
                matched_keywords.add(kw)
                break

    relevance_rate = relevant_chunks / total_chunks if total_chunks > 0 else 0
    keyword_coverage = len(matched_keywords) / len(expected_keywords) if expected_keywords else 0

    return relevance_rate, keyword_coverage, list(matched_keywords)


def run_benchmark(dataset_ids):
    """Run benchmark with all configurations"""
    print("=" * 70)
    print("LOCAL RAG BENCHMARK TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = {
        "timestamp": datetime.now().isoformat(),
        "dataset_ids": dataset_ids,
        "configs": [],
        "summary": {}
    }

    for config in SEARCH_CONFIGS:
        print(f"\n{'='*60}")
        print(f"CONFIG: {config['name']}")
        print(f"  keywords_similarity_weight: {config['keywords_similarity_weight']}")
        print(f"  top_k: {config['top_k']}")
        print(f"  {config['description']}")
        print("-" * 60)

        config_results = {
            "name": config["name"],
            "settings": {
                "keywords_similarity_weight": config["keywords_similarity_weight"],
                "top_k": config["top_k"]
            },
            "questions": [],
            "metrics": {}
        }

        total_chunks = 0
        total_relevant = 0
        total_time = 0
        by_type = {"point": [], "aggregation": [], "semantic": []}

        for q in TEST_QUESTIONS:
            chunks, elapsed = retrieve_chunks(
                dataset_ids,
                q["question"],
                top_k=config["top_k"],
                keywords_similarity_weight=config["keywords_similarity_weight"]
            )

            relevance, coverage, matched = check_chunk_relevance(chunks, q["expected_in_chunks"])

            result = {
                "question": q["question"],
                "type": q["type"],
                "chunks_found": len(chunks),
                "relevance_rate": relevance,
                "keyword_coverage": coverage,
                "matched_keywords": matched,
                "response_time": elapsed
            }
            config_results["questions"].append(result)

            # Aggregate metrics
            total_chunks += len(chunks)
            total_relevant += relevance * len(chunks)
            total_time += elapsed
            by_type[q["type"]].append(coverage)

            # Print result
            status = "PASS" if coverage >= 0.5 else "FAIL"
            print(f"  {status} [{q['type']:11}] \"{q['question']}\" -> {len(chunks)} chunks, "
                  f"relevance: {relevance:.0%}, coverage: {coverage:.0%}, time: {elapsed:.2f}s")

        # Calculate metrics
        avg_relevance = total_relevant / total_chunks if total_chunks > 0 else 0
        avg_time = total_time / len(TEST_QUESTIONS)

        config_results["metrics"] = {
            "total_chunks": total_chunks,
            "avg_relevance": avg_relevance,
            "avg_response_time": avg_time,
            "point_query_score": sum(by_type["point"]) / len(by_type["point"]) if by_type["point"] else 0,
            "aggregation_score": sum(by_type["aggregation"]) / len(by_type["aggregation"]) if by_type["aggregation"] else 0,
            "semantic_score": sum(by_type["semantic"]) / len(by_type["semantic"]) if by_type["semantic"] else 0,
        }

        print(f"\n  METRICS:")
        print(f"    Total Chunks: {total_chunks}")
        print(f"    Avg Relevance: {avg_relevance:.0%}")
        print(f"    Avg Response Time: {avg_time:.2f}s")
        print(f"    Point Query Score: {config_results['metrics']['point_query_score']:.0%}")
        print(f"    Aggregation Score: {config_results['metrics']['aggregation_score']:.0%}")
        print(f"    Semantic Score: {config_results['metrics']['semantic_score']:.0%}")

        results["configs"].append(config_results)
        time.sleep(0.5)  # Rate limiting

    # Overall summary
    print("\n" + "=" * 70)
    print("SUMMARY - CONFIG COMPARISON")
    print("=" * 70)
    print(f"{'Config':<25} {'Point':>8} {'Aggr':>8} {'Semantic':>8} {'Avg Time':>10}")
    print("-" * 70)

    best_config = None
    best_score = 0

    for cfg in results["configs"]:
        m = cfg["metrics"]
        total_score = (m["point_query_score"] + m["aggregation_score"] + m["semantic_score"]) / 3
        print(f"{cfg['name']:<25} {m['point_query_score']:>7.0%} {m['aggregation_score']:>7.0%} "
              f"{m['semantic_score']:>7.0%} {m['avg_response_time']:>9.2f}s")

        if total_score > best_score:
            best_score = total_score
            best_config = cfg["name"]

    results["summary"] = {
        "best_config": best_config,
        "best_score": best_score,
        "recommendation": f"'{best_config}' achieved the highest overall score of {best_score:.0%}"
    }

    print("-" * 70)
    print(f"BEST: {best_config} (score: {best_score:.0%})")

    return results


def main():
    print("Checking available datasets...")

    # List datasets
    datasets = list_datasets()
    if not datasets:
        print("No datasets found! Please create a dataset first.")
        return

    # Show available datasets and filter those with chunks
    print(f"\nFound {len(datasets)} dataset(s):")
    valid_datasets = []
    for i, ds in enumerate(datasets):
        doc_count = ds.get("document_count", 0)
        chunk_count = ds.get("chunk_count", 0)
        name = ds.get('name', 'Unknown')
        # Truncate name for display
        display_name = name[:30] if len(name) > 30 else name
        print(f"  [{i}] {display_name} - {doc_count} docs, {chunk_count} chunks")
        # Only include datasets with chunks
        if chunk_count > 100:
            valid_datasets.append(ds)

    if not valid_datasets:
        print("\nNo datasets with sufficient chunks (>100) found!")
        return

    # Use first valid dataset with most chunks
    valid_datasets.sort(key=lambda x: x.get("chunk_count", 0), reverse=True)
    target_ds = valid_datasets[0]
    dataset_ids = [target_ds.get("id")]

    print(f"\nUsing dataset: {target_ds.get('name')} ({target_ds.get('chunk_count')} chunks)")

    if not dataset_ids:
        print("No valid dataset IDs found!")
        return

    # Run benchmark
    results = run_benchmark(dataset_ids)

    # Save results
    output_file = r"C:\Users\ohjh\ragflow\specs\004-local-rag-benchmark\test-results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
