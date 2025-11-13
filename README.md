# Nokia_project

Dodałem skanowanie 1 pliku
Używam pseudo-streamingu zamiast Hyperscan STREAM mode
Nie wiem co jest problemem nie mogłem inaczej tego zrobic

1. Czytamy plik w chunkach
chunks = []
with open(file, 'rb') as f:
    while chunk := f.read(4096):
        chunks.append(chunk)

2. Łączymy chunki i skanujemy w trybie BLOCK
full_data = b''.join(chunks)
db.scan(full_data, match_event_handler=callback)
```
