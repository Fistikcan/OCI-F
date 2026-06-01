import os
import time
import sys
import json
import shutil
from datetime import datetime
import warnings
import oci

warnings.filterwarnings("ignore", category=FutureWarning)

TEXTS = {
    "TR": {
        "welcome": "Dil Seçimi [TR/EN]: ",
        "json_err": "HATA: 'config.json' bulunamadı!",
        "key_err": "HATA: '{key_name}' bulunamadı!",
        "setup_info": "Sistem kurulumu yapılıyor...",
        "setup_done": "Kurulum tamamlandı!",
        "auth_err": "OCI Yapılandırma Hatası: {err}",
        "attempt": "Deneme Sayısı",
        "status_wait": "Sistem Beklemede",
        "status_req": "İstek Gönderiliyor",
        "success": "BAŞARILI! SUNUCU HESABA EKLENDİ!",
        "err_500": "Kapasite Yok: Stok tükenmiş.",
        "err_429": "Rate Limit: Hız sınırına takıldı.",
        "err_404": "Bulunamadı: Kimlik veya ID hatası.",
        "err_other": "Hata: {err}",
        "region": "Hedef Bölge",
        "hardware": "Donanım Tipi",
        "credit": "by @Fıstıkcan | https://github.com/Fistikcan"
    },
    "EN": {
        "welcome": "Select Language [TR/EN]: ",
        "json_err": "ERROR: 'config.json' not found!",
        "key_err": "ERROR: '{key_name}' not found!",
        "setup_info": "System setup in progress...",
        "setup_done": "Setup completed!",
        "auth_err": "OCI Auth Error: {err}",
        "attempt": "Attempt Count",
        "status_wait": "System Idle",
        "status_req": "Sending Request",
        "success": "SUCCESS! INSTANCE ADDED!",
        "err_500": "Out of Capacity: Stocks depleted.",
        "err_429": "Rate Limit: Too many requests.",
        "err_404": "Not Found: Invalid IDs.",
        "err_other": "Error: {err}",
        "region": "Target Region",
        "hardware": "Hardware Spec",
        "credit": "by @Fıstıkcan | https://github.com/Fistikcan"
    }
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_language():
    clear_screen()
    if sys.platform.startswith('win'):
        os.system('color 0a')
        os.system('title OCI-F STOK AVCISI')
    print("\n" + "="*50)
    print("      OCI-F BOT INITIALIZATION PROTOCOL")
    print("="*50)
    while True:
        choice = input("\n [?] Dil Seçimi / Select Language (TR/EN): ").strip().upper()
        if choice in ["TR", "EN"]:
            return choice

def setup_oci_environment(lang):
    t = TEXTS[lang]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "config.json")
    if not os.path.exists(json_path):
        print("\n [!] " + t["json_err"])
        sys.exit(1)
    with open(json_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    key_name = config_data.get("private_key_name", "key.pem")
    key_source_path = os.path.join(current_dir, key_name)
    if not os.path.exists(key_source_path):
        print("\n [!] " + t["key_err"].format(key_name=key_name))
        sys.exit(1)
    print("\n [*] " + t["setup_info"])
    user_home = os.path.expanduser("~")
    oci_dir = os.path.join(user_home, ".oci")
    if not os.path.exists(oci_dir):
        os.makedirs(oci_dir)
    key_dest_path = os.path.join(oci_dir, key_name)
    shutil.copy(key_source_path, key_dest_path)
    oci_config_path = os.path.join(oci_dir, "config")
    config_content = f"[DEFAULT]\nuser={config_data['user_ocid']}\nfingerprint={config_data['fingerprint']}\ntenancy={config_data['tenancy_ocid']}\nregion={config_data['region']}\nkey_file={key_dest_path.replace('\\', '/')}\n"
    with open(oci_config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(" [+] " + t["setup_done"])
    time.sleep(1)
    return config_data

def draw_interface(lang, config_data, attempt, status, message, timer_bar=""):
    t = TEXTS[lang]
    clear_screen()
    region = config_data['region'].upper()
    ocpus = config_data['ocpus']
    ram = config_data['memory_in_gbs']
    ui = f"""
╔═════════════════════════════════════════════════════════════════════════╗
║                                                                         ║
║       ██████╗  ██████╗ ██╗      ███████╗                                ║
║      ██╔═══██╗██╔════╝ ██║      ██╔════╝                                ║
║      ██║   ██║██║      ██║█████╗█████╗                                  ║
║      ██║   ██║██║      ██║╚════╝██╔══╝                                  ║
║      ╚██████╔╝╚██████╗ ██║      ██║                                     ║
║       ╚═════╝  ╚═════╝ ╚═╝      ╚═╝                                     ║
║                                                                         ║
║                 {t['credit']:^55} ║
╠═════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║  [*] {t['region']:<14} : [ {region} ]                                     
║  [*] {t['hardware']:<14} : [ {ocpus} vCPU / {ram} GB RAM ]                           
║                                                                         ║
╠═════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║  [#] {t['attempt']:<14} : {attempt:<50} ║
║  [>] Durum          : {status:<50} ║
║  [!] Log            : {message:<50} ║
║                                                                         ║
║  {timer_bar:<71}║
╚═════════════════════════════════════════════════════════════════════════╝
"""
    print(ui, end="")

def interpret_error(error_message, lang):
    t = TEXTS[lang]
    if "Out of host capacity" in error_message or "500" in error_message:
        return t["err_500"]
    elif "TooManyRequests" in error_message or "429" in error_message:
        return t["err_429"]
    elif "NotAuthorizedOrNotFound" in error_message or "404" in error_message:
        return t["err_404"]
    else:
        return t["err_other"].format(err=error_message[:35] + "...")

def create_progress_bar(current, total=30):
    filled_len = int(30 * (total - current) // total)
    bar = '█' * filled_len + '░' * (30 - filled_len)
    return f"Status: [{bar}] {current:02d}s"

def main():
    lang = get_language()
    t = TEXTS[lang]
    config_data = setup_oci_environment(lang)
    try:
        oci_config = oci.config.from_file()
        compute_client = oci.core.ComputeClient(oci_config)
    except Exception as e:
        print("\n" + t["auth_err"].format(err=str(e)))
        sys.exit(1)
    INSTANCE_DETAILS = oci.core.models.LaunchInstanceDetails(
        availability_domain="lZPw:EU-MARSEILLE-1-AD-1",
        compartment_id=config_data["tenancy_ocid"],
        shape="VM.Standard.A1.Flex",
        display_name="Virtual Machine",
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=config_data["ocpus"], memory_in_gbs=config_data["memory_in_gbs"]),
        source_details=oci.core.models.InstanceSourceViaImageDetails(source_type="image", image_id=config_data["image_id"], boot_volume_size_in_gbs=config_data["boot_volume_size_in_gbs"]),
        create_vnic_details=oci.core.models.CreateVnicDetails(assign_public_ip=True, display_name="bugraefevm", subnet_id=config_data["subnet_id"], assign_private_dns_record=True),
        instance_options=oci.core.models.InstanceOptions(are_legacy_imds_endpoints_disabled=True),
        metadata={"ssh_authorized_keys": config_data["ssh_authorized_keys"]}
    )
    attempt = 1
    last_msg = "Booting..."
    while True:
        for i in range(4):
            loading_anim = f"Processing {'.' * (i % 4)}"
            draw_interface(lang, config_data, attempt, t["status_req"], last_msg, loading_anim)
            time.sleep(0.3)
        try:
            response = compute_client.launch_instance(launch_instance_details=INSTANCE_DETAILS)
            if response.status and response.status == 200:
                draw_interface(lang, config_data, attempt, t["success"], f"ID: {response.data.id[:25]}...", ">>> SUCCESS <<<")
                sys.stdout.write('\a')
                sys.stdout.flush()
                break
        except oci.exceptions.ServiceError as e:
            last_msg = interpret_error(str(e), lang)
        except Exception as e:
            last_msg = interpret_error(str(e), lang)
        for seconds in range(30, 0, -1):
            timer_anim = create_progress_bar(seconds)
            draw_interface(lang, config_data, attempt, t["status_wait"], last_msg, timer_anim)
            time.sleep(1)
        attempt += 1

if __name__ == "__main__":
    main()
