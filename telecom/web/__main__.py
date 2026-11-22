"""Ponto de entrada para executar o servidor web: python -m telecom.web"""

import argparse
import sys
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Servidor Web do Trabalho Telecom 2026.2")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de escuta (padrão: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Porta TCP (padrão: 8000)")
    parser.add_argument("--reload", action="store_true", help="Recarregar em caso de alteração no código")
    args = parser.parse_args()

    print(f"Iniciando interface web em http://{args.host}:{args.port}")
    uvicorn.run("telecom.web.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
