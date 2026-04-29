"""
Chemical Product Knowledge Base — Pesticide/Herbicide/Fungicide catalog
with alternative finder based on active ingredient matching.
"""

PRODUCTS = [
    {"id": 1, "name": "GlyphoMax 41%", "category": "HERBICIDE", "toxicity": "HIGH",
     "active_ingredient": "Glyphosate 41% SL", "dosage": "800ml-1L/Acre",
     "desc": "Systemic non-selective weed killer", "price": 550, "manufacturer": "Excel Crop Care"},
    {"id": 2, "name": "EcoClear WeedMaster", "category": "HERBICIDE", "toxicity": "MODERATE",
     "active_ingredient": "Ammonium Salt of Glyphosate 71% SG", "dosage": "500-600g/Acre",
     "desc": "Water-soluble granule herbicide", "price": 450, "manufacturer": "UPL"},
    {"id": 3, "name": "Paraquat Dichloride 24% SL", "category": "HERBICIDE", "toxicity": "HIGH",
     "active_ingredient": "Paraquat 24% SL", "dosage": "600-800ml/Acre",
     "desc": "Contact herbicide for quick weed burn", "price": 520, "manufacturer": "Syngenta"},
    {"id": 4, "name": "Mancozeb 75% WP", "category": "FUNGICIDE", "toxicity": "LOW",
     "active_ingredient": "Mancozeb 75% WP", "dosage": "2-2.5g/L water",
     "desc": "Broad-spectrum protective fungicide for blight", "price": 280, "manufacturer": "Indofil"},
    {"id": 5, "name": "Copper Oxychloride 50% WP", "category": "FUNGICIDE", "toxicity": "LOW",
     "active_ingredient": "Copper Oxychloride 50% WP", "dosage": "2.5-3g/L water",
     "desc": "Organic-approved fungicide for downy mildew", "price": 320, "manufacturer": "Bayer"},
    {"id": 6, "name": "Carbendazim 50% WP", "category": "FUNGICIDE", "toxicity": "MODERATE",
     "active_ingredient": "Carbendazim 50% WP", "dosage": "1-2g/L water",
     "desc": "Systemic fungicide for powdery mildew", "price": 250, "manufacturer": "BASF"},
    {"id": 7, "name": "Imidacloprid 17.8% SL", "category": "INSECTICIDE", "toxicity": "MODERATE",
     "active_ingredient": "Imidacloprid 17.8% SL", "dosage": "0.5ml/L water",
     "desc": "Systemic insecticide for sucking pests", "price": 380, "manufacturer": "Bayer"},
    {"id": 8, "name": "Neem Oil 1500 PPM", "category": "INSECTICIDE", "toxicity": "LOW",
     "active_ingredient": "Azadirachtin 1500 PPM", "dosage": "3-5ml/L water",
     "desc": "Organic bio-pesticide for aphids and whitefly", "price": 220, "manufacturer": "Multiplex"},
    {"id": 9, "name": "Chlorpyrifos 20% EC", "category": "INSECTICIDE", "toxicity": "HIGH",
     "active_ingredient": "Chlorpyrifos 20% EC", "dosage": "2-2.5ml/L water",
     "desc": "Broad-spectrum contact insecticide", "price": 340, "manufacturer": "Dow"},
    {"id": 10, "name": "Thiamethoxam 25% WG", "category": "INSECTICIDE", "toxicity": "MODERATE",
     "active_ingredient": "Thiamethoxam 25% WG", "dosage": "0.3-0.5g/L water",
     "desc": "Second-gen neonicotinoid for stem borers", "price": 420, "manufacturer": "Syngenta"},
    {"id": 11, "name": "Metalaxyl 35% WS", "category": "FUNGICIDE", "toxicity": "LOW",
     "active_ingredient": "Metalaxyl 35% WS", "dosage": "2g/kg seed",
     "desc": "Seed treatment fungicide for root rot", "price": 350, "manufacturer": "Rallis"},
    {"id": 12, "name": "2,4-D Amine Salt 58% SL", "category": "HERBICIDE", "toxicity": "MODERATE",
     "active_ingredient": "2,4-D 58% SL", "dosage": "1-1.5L/Acre",
     "desc": "Selective herbicide for broadleaf weeds", "price": 290, "manufacturer": "Dhanuka"},
]

# Treatment recommendations per disease
DISEASE_TREATMENTS = {
    "late_blight": [
        {"id": "chemical", "type": "CHEMICAL", "product_id": 4,
         "desc": "Fast-acting fungicide. Apply 2-2.5g per liter of water immediately."},
        {"id": "organic", "type": "ORGANIC", "product_id": 5,
         "desc": "Approved for organic use. Apply preventatively or at first sign."},
    ],
    "powdery_mildew": [
        {"id": "chemical", "type": "CHEMICAL", "product_id": 6,
         "desc": "Systemic fungicide. Apply 1g/L every 10 days."},
        {"id": "organic", "type": "ORGANIC", "product_id": 8,
         "desc": "Neem oil spray. Apply 5ml/L every 7 days."},
    ],
    "aphids": [
        {"id": "chemical", "type": "CHEMICAL", "product_id": 7,
         "desc": "Apply 0.5ml/L as foliar spray. Effective for 14 days."},
        {"id": "organic", "type": "ORGANIC", "product_id": 8,
         "desc": "Neem oil 3ml/L. Safe for beneficial insects."},
    ],
}


def analyze_product(name: str) -> dict:
    """Find a product and return alternatives."""
    product = next((p for p in PRODUCTS if name.lower() in p["name"].lower()), None)
    if not product:
        # Search by active ingredient
        product = next((p for p in PRODUCTS if name.lower() in p["active_ingredient"].lower()), None)
    if not product:
        return {"status": "error", "message": f"Product '{name}' not found in database"}

    # Find alternatives in same category
    alts = []
    for p in PRODUCTS:
        if p["id"] == product["id"]:
            continue
        if p["category"] == product["category"]:
            # Calculate match score
            same_ingredient = product["active_ingredient"].split()[0].lower() in p["active_ingredient"].lower()
            match = 98 if same_ingredient else (85 if p["category"] == product["category"] else 60)
            safety = "Safer" if _tox_rank(p["toxicity"]) < _tox_rank(product["toxicity"]) else \
                     ("Same" if p["toxicity"] == product["toxicity"] else "Higher Risk")
            alts.append({
                "name": p["name"], "desc": p["active_ingredient"],
                "match": match, "price": p["price"],
                "price_note": f"{round((product['price'] - p['price'])/product['price']*100)}%" if p["price"] < product["price"] else "Similar",
                "efficacy": round(4.0 + match/100, 1),
                "safety": safety,
                "safety_color": "#2E7D32" if safety == "Safer" else ("#E65100" if safety == "Same" else "#C62828"),
            })
    alts.sort(key=lambda x: x["match"], reverse=True)

    return {"status": "success", "product": product, "alternatives": alts[:3]}


def get_treatments(disease: str) -> list:
    """Get treatment recommendations for a detected disease."""
    key = disease.lower().replace(" ", "_").replace("___", "_").replace("tomato_", "")
    treatments = DISEASE_TREATMENTS.get(key, DISEASE_TREATMENTS.get("late_blight"))
    result = []
    for t in treatments:
        prod = next((p for p in PRODUCTS if p["id"] == t["product_id"]), None)
        if prod:
            result.append({**t, "name": prod["name"], "product": prod})
    return result


def _tox_rank(level):
    return {"LOW": 1, "MODERATE": 2, "HIGH": 3}.get(level, 2)
