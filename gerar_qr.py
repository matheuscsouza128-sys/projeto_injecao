import qrcode

base_url = "https://projeto-injecao.onrender.com"

for i in range(1, 11):
    url = f"{base_url}/maquina/{i}"
    
    img = qrcode.make(url)
    img.save(f"qr_maquina_{i}.png")

print("QR Codes atualizados!")