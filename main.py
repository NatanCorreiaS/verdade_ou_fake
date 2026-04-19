import os
from dotenv import load_dotenv


def main():
    """Load environment variables and print the configured API key.

    This is a minimal entry point used to verify that `.env` loading works.
    """
    load_dotenv()

    my_key = os.getenv("API_KEY")

    print(f"A chave recuperada foi: {my_key}")


if __name__ == "__main__":
    main()
    