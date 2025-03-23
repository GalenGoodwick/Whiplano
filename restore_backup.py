import asyncio
import asyncmy
import os
from dotenv import load_dotenv
load_dotenv()
DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST"),
    "port": 3306,
    "user": os.getenv("DATABASE_USERNAME"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "database": os.getenv("DATABASE_NAME")
}


async def restore_db(txt_file: str):
    connection = None
    try:
        connection = await asyncmy.connect(**DB_CONFIG)
        print(type(connection))
        async with connection.cursor() as cursor:
            await cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
            with open(txt_file, "r", encoding="utf-8") as f:  # Open text file
                statement = ""
                for line in f:
                    line = line.strip()

                    # Ignore comments and empty lines
                    if not line or line.startswith("--") or line.startswith("/*"):
                        continue

                    statement += line + " "  # Append to current SQL statement

                    if line.endswith(";"):  # Execute when statement is complete
                        await cursor.execute(statement)
                        statement = ""  # Reset for next statement

            await connection.commit()
            print("✅ Database restored successfully!")

    except Exception as e:
        if connection:
            await connection.rollback()
        print(f"❌ Error restoring database: {e}")

    finally:
        if connection:
            print(type(connection))


# Run the restore process
asyncio.run(restore_db("backup.txt"))