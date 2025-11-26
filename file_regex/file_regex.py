class FileRegex():
    def __init__(self, filename):
        self.plik = filename
        open(self.plik, "a", encoding="utf-8").close()
    def add_element(self,text):
        if not self.exist(text):
            with open(self.plik, "a", encoding="utf-8") as f:
                f.write(text.strip() + "\n")

    def delete_element(self,text):
        with open(self.plik, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(self.plik, "w", encoding="utf-8") as f:
            for line in lines:
                if line.strip() != text.strip():
                    f.write(line)
        return
    def choose_elements(self):
        pass
    def exist(self,text):
        with open(self.plik, "r",encoding="utf-8") as f:
            for line in f:
                if line.strip()==text:
                    return True
        return False
    def elements(self):
        patterns=[] #potem popraw na choose_elements
        with open(self.plik, "r",encoding="utf-8") as f:
            for line in f:
                text = line.strip()
                if text:
                    before_comma = text.split(",", 1)[0].strip()
                    # print(before_comma)
                    patterns.append(before_comma)
        return patterns

 