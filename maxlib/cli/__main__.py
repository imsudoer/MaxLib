"""
CLI entry point for MaxLib tools (login, info, interactive shell).
"""
import argparse
import asyncio
import sys
from ..client.client import MaxClient


def cli_main() -> None:
    parser = argparse.ArgumentParser(description="MaxLib CLI - Tools for MAX Messenger")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: login
    login_parser = subparsers.add_parser("login", help="Authenticate and save session")
    login_parser.add_argument("-s", "--session", default="me", help="Session name or file (default: me)")
    login_parser.add_argument("-p", "--phone", default=None, help="Phone number (+7...)")

    # Command: info
    info_parser = subparsers.add_parser("info", help="Print account and session info")
    info_parser.add_argument("-s", "--session", default="me", help="Session name or file (default: me)")

    # Command: shell
    shell_parser = subparsers.add_parser("shell", help="Launch interactive Python REPL with connected client")
    shell_parser.add_argument("-s", "--session", default="me", help="Session name or file (default: me)")

    args = parser.parse_args()

    if args.command == "login":
        async def do_login():
            client = MaxClient(session=args.session, phone=args.phone)
            user = await client.start(phone=args.phone)
            print(f"[+] Successfully logged in as: {user.name} (ID: {user.id})")
            print(f"[+] Session saved to: {client.session.path if hasattr(client.session, 'path') else 'session'}")
            await client.stop()

        asyncio.run(do_login())

    elif args.command == "info":
        async def do_info():
            client = MaxClient(session=args.session)
            if not client.session.token:
                print(f"[-] No token found in session '{args.session}'. Run 'python -m maxlib login' first.")
                return
            user = await client.start()
            print("=" * 40)
            print(f" User ID:      {user.id}")
            print(f" Full Name:    {user.name}")
            print(f" Phone:        {user.phone}")
            print(f" Avatar URL:   {user.avatar_url or 'None'}")
            print("=" * 40)
            await client.stop()

        asyncio.run(do_info())

    elif args.command == "shell":
        import code
        async def init_client():
            c = MaxClient(session=args.session)
            await c.start()
            return c

        client = asyncio.run(init_client())
        banner = (
            f"[*] MaxLib Interactive Shell\n"
            f"[*] Connected as: {client.me.name if client.me else 'User'} (ID: {client.me.id if client.me else '?'})\n"
            f"[*] Client variable available as 'client'\n"
        )
        code.interact(banner=banner, local={"client": client, "asyncio": asyncio})

    else:
        parser.print_help()


if __name__ == "__main__":
    cli_main()
