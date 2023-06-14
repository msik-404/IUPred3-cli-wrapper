import asyncio
from dotenv import load_dotenv
from src import wrapper

if __name__ == "__main__":
    load_dotenv()
    args = wrapper.parse_args()
    asyncio.run(wrapper.main(args))
