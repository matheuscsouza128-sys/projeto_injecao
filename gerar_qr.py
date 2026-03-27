import qrcode

# Quantidade de máquinas (ajusta depois)
for i in range(1, 11):
    url = f"http://127.0.0.1:5000/maquina/{i}"
    
    img = qrcode.make(url)
    img.save(f"qr_maquina_{i}.png")

print("QR Codes gerados com sucesso!")