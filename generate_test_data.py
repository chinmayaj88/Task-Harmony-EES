import json
import random
import re

# Constants and Data Pools
PORTS = [
    {"code": "INMAA", "name": "Chennai", "aliases": ["Chennai", "Madras", "MAA", "Cheenai", "Chennai Port"]},
    {"code": "CNSHA", "name": "Shanghai", "aliases": ["Shanghai", "SHA", "Shangai", "Shengai"]},
    {"code": "SGSIN", "name": "Singapore", "aliases": ["Singapore", "SIN", "Singapor", "S'pore"]},
    {"code": "AEJEA", "name": "Jebel Ali", "aliases": ["Jebel Ali", "JEA", "Jebel Ali Port", "Dubai (Jebel Ali)"]},
    {"code": "KRPUS", "name": "Busan", "aliases": ["Busan", "Pusan", "BUS", "PUS"]},
    {"code": "DEHAM", "name": "Hamburg", "aliases": ["Hamburg", "HAM", "Hamburgh"]},
    {"code": "USLAX", "name": "Los Angeles", "aliases": ["Los Angeles", "LAX", "L.A.", "Los Angles"]},
    {"code": "INBLR", "name": "Bangalore", "aliases": ["Bangalore", "BLR", "Bengaluru", "ICD Bangalore"]},
    {"code": "INNSA", "name": "Nhava Sheva", "aliases": ["Nhava Sheva", "NSA", "Nava Sheva", "Mumbai (Nhava Sheva)"]},
    {"code": "MYPKG", "name": "Port Klang", "aliases": ["Port Klang", "PKG", "Port Kelang"]},
    {"code": "CNNSA", "name": "Nansha", "aliases": ["Nansha", "NSA (China)"]}, # careful with NSA duplications in text, usually context clears it
    {"code": "TWKEL", "name": "Keelung", "aliases": ["Keelung", "KEL", "Keelung TW"]},
]

INCOTERMS = ["FOB", "EXW", "CIF", "DDP", "DAP", "FCA"]
COMMODITIES = [
    "Auto Parts", "Textiles", "Machinery", "Chemicals", "Electronics", 
    "Furniture", "Garments", "Plastic Goods", "Steel Pipes", "Toys"
]

SPAM_PHRASES = [
    "\n\nSent from my iPhone", 
    "\n\nGet 50% off on your next shipment! Visit our site.", 
    "\n\nAUTO-REPLY: I am out of office.", 
    "\n\nCONFIDENTIALITY NOTICE: The contents of this email message and any attachments are intended solely for the addressee(s) and may contain confidential and/or privileged information and may be legally protected from disclosure.",
    "\n\nBuy crypto now!!",
    "\n\nPlease consider the environment before printing this email.",
    "\n\nVIRUS FREE SCANNED BY AVAST.",
]

BROKEN_ENGLISH_PHRASES = [
    "kindly do the needful", "pls revert back asap", "we are wanting to ship", 
    "hope you are doing well good morning", "regarding the subject matter", 
    "attached herewith the details", "giving best rats pls", "urgent shippment request"
]

# Generators
def get_random_port(exclude_code=None):
    choice = random.choice(PORTS)
    while choice["code"] == exclude_code:
        choice = random.choice(PORTS)
    return choice

def introduce_typos(text, probability=0.1):
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < probability and chars[i].isalpha():
            if random.random() < 0.5:
                # swap
                if i < len(chars) - 1:
                    chars[i], chars[i+1] = chars[i+1], chars[i]
            else:
                # drop
                chars[i] = ""
    return "".join(chars)

def generate_email_data(index):
    # Setup Logic
    origin = get_random_port()
    dest = get_random_port(exclude_code=origin["code"])
    
    # Decide direction mainly for product line (simulated logic)
    # If Origin is India -> Export, Else Import (simplified assumption for ground truth generation)
    product_line = "pl_sea_export_lcl" if origin["code"].startswith("IN") else "pl_sea_import_lcl"
    
    incoterm = random.choice(INCOTERMS)
    weight = round(random.uniform(100, 5000), 2)
    cbm = round(weight / random.uniform(200, 1000), 2) # Rough density
    if cbm < 0.1: cbm = 0.5
    
    is_dangerous = random.choice([True, False, False, False]) # 25% chance
    commodity = random.choice(COMMODITIES)
    
    # Construct Body
    template_type = random.choice(["clean", "messy", "short", "long_spam"])
    
    origin_str = random.choice(origin["aliases"])
    dest_str = random.choice(dest["aliases"])
    
    body = ""
    subject = ""
    
    if template_type == "clean":
        subject = f"Enquiry: {origin_str} to {dest_str}"
        body = f"Dear Team,\n\nPlease quote for {commodity}.\nOrigin: {origin_str}\nDest: {dest_str}\nWeight: {weight} kgs\nVolume: {cbm} cbm\nIncoterm: {incoterm}\nDG: {'Yes' if is_dangerous else 'No'}\n\nRegards,\nClient"
        
    elif template_type == "messy":
        subject = f"URGENT!!!! shipment {origin_str} -> {dest_str}"
        phrase = random.choice(BROKEN_ENGLISH_PHRASES)
        body = f"Hi,\n\n{phrase}.\nWe hv shipment form {introduce_typos(origin_str)} to {introduce_typos(dest_str)}.\nPls give rates.\n\nDetails:\nComm: {commodity}\nWght: {int(weight)}kgs (approx)\nVol: {cbm} m3\nTerm: {incoterm}\n\n{'Need DG rates!!' if is_dangerous else 'Non-haz cargo.'}\n\nThx."
        
    elif template_type == "short":
        subject = f"{origin_str}-{dest_str} rate"
        body = f"{cbm}cbm, {weight}kg. {origin_str} to {dest_str}. {incoterm}. {'DG' if is_dangerous else ''}."
        
    elif template_type == "long_spam":
        subject = f"Re: Fwd: Shipment Enquiry {commodity}"
        body = f"Dear Sir/Madam,\n\nHope this email finds you well.\n\nWe have a new requirement. Please see below details and provide your best ocean freight charges locally and destination wise.\n\nPOL: {origin_str}\nPOD: {dest_str}\nItem: {commodity}\nGross Weight: {weight} KG\nMeasurement: {cbm} CBM\nTerms of Shipment: {incoterm}\nDangerous Goods: {'YES (Class 3)' if is_dangerous else 'NO'}\n\nLooking forward to your swift reply.\n\n{random.choice(SPAM_PHRASES)}\n{random.choice(SPAM_PHRASES)}"

    # Add random noise or typos to body in 'messy' or 'short' cases sometimes
    if template_type in ["messy", "short"] and random.random() < 0.3:
        body = introduce_typos(body, probability=0.02)

    # Construct Extraction Result (Ground Truth)
    # Note: ground truth expects standard names, extracting from our known logic
    
    ground_truth = {
        "id": f"TEST_EMAIL_{index:03d}",
        "reasoning": "Ground truth generated from synthesis script.",
        "product_line": product_line,
        "origin_port_code": origin["code"],
        "origin_port_name": origin["name"], # The canonical name
        "destination_port_code": dest["code"],
        "destination_port_name": dest["name"], # The canonical name
        "incoterm": incoterm if incoterm else "FOB", # defaulting logic in schema is FOB
        "cargo_weight_kg": weight,
        "cargo_cbm": cbm,
        "is_dangerous": is_dangerous
    }
    
    # Handle implicit FOB if omitted (simulated)
    # logic: if incoterm not in text, schema default is FOB.
    # But validation logic is: if not found, None? 
    # Schema says: incoterm: Optional[str] = Field("FOB")
    # So if extraction misses it, it defaults.
    # In my generation, I always put it in text, so it should be found.
    
    email_entry = {
        "id": f"TEST_EMAIL_{index:03d}",
        "subject": subject,
        "body": body,
        "sender_email": f"user{index}@example.com",
        "to_emails": "sales@logistics.com",
        "cc_emails": ""
    }
    
    return email_entry, ground_truth

# Generate 50
emails = []
ground_truths = []
used_ports = set()

for i in range(1, 51):
    em, gt = generate_email_data(i)
    emails.append(em)
    ground_truths.append(gt)
    used_ports.add(gt["origin_port_code"])
    used_ports.add(gt["destination_port_code"])

# Write files
with open("c:/Users/jenac/Downloads/Task-Harmony-EES/data/emails_test_difficult.json", "w") as f:
    json.dump(emails, f, indent=2)

with open("c:/Users/jenac/Downloads/Task-Harmony-EES/data/ground_truth_test_difficult.json", "w") as f:
    json.dump(ground_truths, f, indent=2)

# Write ref
ref_list = [p for p in PORTS if p["code"] in used_ports]
with open("c:/Users/jenac/Downloads/Task-Harmony-EES/data/port_codes_test_ref.json", "w") as f:
    json.dump(ref_list, f, indent=2)

print("Generated 50 test emails.")
