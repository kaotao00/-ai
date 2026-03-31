import argparse
import json
import sys
from pathlib import Path

from ai_butler.api_service import PrivateAIAssistantService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI管家私有化问答系统")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser("ask", help="发起问答")
    ask_parser.add_argument("--question", required=True, help="用户问题")
    ask_parser.add_argument("--top-k", type=int, default=4, help="召回文档数量")

    ingest_parser = subparsers.add_parser("ingest", help="导入文档")
    ingest_parser.add_argument("--file", required=True, help="文件路径")
    ingest_parser.add_argument("--category", default="general", help="文档分类")
    ingest_parser.add_argument("--source", default="企业内部资料", help="文档来源")

    list_parser = subparsers.add_parser("list", help="查看知识库文档")
    list_parser.add_argument("--limit", type=int, default=20, help="显示数量")
    return parser


def main() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent
    service = PrivateAIAssistantService(base_dir=base_dir)

    if args.command == "ask":
        result = service.ask(question=args.question, top_k=args.top_k)
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    elif args.command == "ingest":
        result = service.ingest_file(
            file_path=Path(args.file),
            category=args.category,
            source=args.source,
        )
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    elif args.command == "list":
        result = service.list_documents(limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
