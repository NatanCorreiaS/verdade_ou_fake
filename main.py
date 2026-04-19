import os
from dotenv import load_dotenv


def main():
    load_dotenv()

    my_key = os.getenv("API_KEY")

    print(f"A chave recuperada foi: {my_key}")


if __name__ == "__main__":
    main()
    