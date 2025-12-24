
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.llm_service import llm_service
import json

def test_extraction():
    test_cases = [
        {
            "name": "Long Address",
            "transcript": "oke alamat lengkap rumah saya adalah Jalan Merdeka Nomor 10 RT 01 RW 02 Kelurahan Maju Kecamatan Mundur Kota Jakarta Pusat Provinsi DKI Jakarta dan kode pos 12345 lalu warna rumah saya biru",
            "expected_contains": "Jalan Merdeka Nomor 10 RT 01 RW 02 Kelurahan Maju Kecamatan Mundur Kota Jakarta Pusat Provinsi DKI Jakarta"
        },
        {
            "name": "Short Address",
            "transcript": "saya tinggal di Dusun Suka Maju di dekat pasar",
            "expected_contains": "Dusun Suka Maju"
        },
        {
            "name": "Kabupaten Normalization",
            "transcript": "saya tinggal di Kabupaten Sleman",
            "expected_contains": "Kab. Sleman"
        }
    ]


    with open("test_output_log.txt", "w", encoding="utf-8") as f:
        f.write("Running Address Extraction Tests...\n\n")
        
        for case in test_cases:
            f.write(f"Testing: {case['name']}\n")
            f.write(f"Transcript: {case['transcript']}\n")
            
            try:
                result = llm_service.extract_information(case['transcript'])
                extracted_address = result.get('alamat')
                
                f.write(f"Extracted Address: {extracted_address}\n")
                
                if extracted_address and case['expected_contains'] in extracted_address:
                    f.write("✅ PASS\n")
                else:
                    f.write("❌ FAIL\n")
                    f.write(f"Expected to contain: {case['expected_contains']}\n")
                    
            except Exception as e:
                f.write(f"❌ ERROR: {e}\n")
            
            f.write("-" * 30 + "\n")

if __name__ == "__main__":
    test_extraction()
