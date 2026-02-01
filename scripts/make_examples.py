import os
from generate_data import TableBPMNGenerator

# Сколько примеров хотим увидеть
NUM_EXAMPLES = 5

OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
MD_FILE = os.path.join(OUTPUT_DIR, "example.md")

os.makedirs(IMAGES_DIR, exist_ok=True)


def main():
    gen = TableBPMNGenerator()

    md_lines = []
    md_lines.append("# Примеры сгенерированных BPMN-диаграмм\n")
    md_lines.append("Ниже приведены примеры диаграмм и их табличное описание.\n")

    for i in range(NUM_EXAMPLES):
        fname = f"demo_{i:02d}"
        img_name, table_md = gen.generate(fname)

        md_lines.append(f"---\n")
        md_lines.append(f"## Пример {i+1}\n")
        md_lines.append(f"![{fname}](images/{img_name})\n")
        md_lines.append("\n### Описание процесса\n")
        md_lines.append(table_md)
        md_lines.append("\n")

    with open(MD_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("Готово!")
    print(f"Файл с примерами: {MD_FILE}")


if __name__ == "__main__":
    main()
