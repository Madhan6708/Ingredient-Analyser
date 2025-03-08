import cv2
import pytesseract
import openpyxl
import wikipediaapi
import streamlit as st
from PIL import Image
import numpy as np

wb = openpyxl.load_workbook("harmful_ingredients.xlsx")
sheet = wb.active

health_risks = {
    "Diabetes": ["sugar", "high fructose corn syrup", "aspartame", "maltodextrin", "dextrose", "glucose", "sucrose", "honey", "agave syrup"],
    "High Blood Pressure": ["sodium", "monosodium glutamate (MSG)", "caffeine", "salt", "preservatives like sodium benzoate", "processed meats", "hydrogenated oils"],
    "Thyroid Issues": ["soy", "certain preservatives", "fluoride", "cruciferous vegetables (in excess)", "artificial food coloring", "nitrate preservatives"],
    "Kidney Disease": ["high sodium", "phosphates", "potassium additives", "processed foods", "artificial sweeteners"],
    "Heart Disease": ["trans fats", "saturated fats", "cholesterol", "hydrogenated oils", "processed meats", "high sodium", "refined carbs"],
    "Liver Disease": ["alcohol", "high fructose corn syrup", "excessive processed fats", "artificial additives", "pesticide residues"],
    "Gastrointestinal Issues": ["artificial sweeteners", "high fructose corn syrup", "sorbitol", "carrageenan", "processed dairy", "fried foods"],
    "Skin Conditions (Acne, Eczema, Psoriasis)": ["dairy", "refined sugar", "artificial flavors", "processed oils", "gluten (for some individuals)"],
    "Migraines": ["MSG", "caffeine", "artificial sweeteners", "processed meats", "aged cheese", "nitrates", "chocolate"],
    "Joint Pain/Arthritis": ["processed sugars", "nightshade vegetables (for some)", "excess omega-6 fatty acids", "gluten", "alcohol"],
    "Allergies & Asthma": ["sulfites", "food dyes", "preservatives like benzoates", "processed dairy", "gluten"],
    "Cancer Risks": ["processed meats", "nitrates", "artificial sweeteners", "refined sugars", "highly processed foods", "pesticide residues"]
}

# Initialize session state
if "captured" not in st.session_state:
    st.session_state["captured"] = False
if "image" not in st.session_state:
    st.session_state["image"] = None

# Function to fetch definitions from Wikipedia
def fetch_wikipedia_definition(ingredient):
    wiki_wiki = wikipediaapi.Wikipedia(user_agent="IngredientInspector/1.0", language="en")
    page = wiki_wiki.page(ingredient)
    return page.summary[:300] if page.exists() else "Definition not found."

# Function to check for unsafe ingredients
def check_safety(product_text, user_conditions):
    unsafe_ingredients = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        ingredient, effect = row[:2]  # Assume second column contains effects
        if ingredient and ingredient.lower() in product_text.lower():
            unsafe_ingredients.append((ingredient.lower(), effect))
    
    # Check for health condition-specific risks
    additional_risks = []
    for condition in user_conditions:
        if condition in health_risks:
            for restricted in health_risks[condition]:
                if restricted.lower() in product_text.lower():
                    additional_risks.append((restricted.lower(), f"Avoid due to {condition}"))
    
    return unsafe_ingredients + additional_risks

# Streamlit UI Styling
st.set_page_config(page_title="Ingredient Analyser", layout="wide")
st.title("🧪 Ingredient Analyser")
st.subheader("Check product ingredients for safety and health risks.")

# User health conditions selection
user_conditions = st.multiselect("Select your health conditions:", list(health_risks.keys()))

option = st.radio("Choose Input Method:", ("📷 Capture from Camera", "📁 Upload Image"))

captured_image = None
if option == "📷 Capture from Camera":
    captured_image = st.camera_input("Take a picture of the product ingredients")
    if captured_image:
        st.session_state["captured"] = True
        st.session_state["image"] = captured_image
        st.image(captured_image, caption="Captured Image", use_column_width=True)
elif option == "📁 Upload Image":
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png", "bmp"])
    if uploaded_file:
        captured_image = Image.open(uploaded_file)
        st.session_state["captured"] = True
        st.session_state["image"] = captured_image
        st.image(captured_image, caption="Uploaded Image", use_column_width=True)

if st.session_state["captured"] and st.session_state["image"]:
    if option == "📷 Capture from Camera":
        # Convert the captured image to a NumPy array
        image_np = np.array(Image.open(st.session_state["image"]))
    else:
        # Convert the uploaded image to a NumPy array
        image_np = np.array(st.session_state["image"])
    
    # Ensure the image is in the correct format (3-channel RGB)
    if image_np.ndim == 2:  # If grayscale, convert to RGB
        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
    elif image_np.ndim == 3 and image_np.shape[2] == 4:  # If RGBA, convert to RGB
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
    else:
        # Assume it's already in RGB format
        pass
    
    # Convert the image to BGR format (required by OpenCV)
    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    
    with st.spinner("🔍 Extracting text from the image..."):
        product_text = pytesseract.image_to_string(image_np)
    
    st.subheader("📝 Extracted Text:")
    st.text_area("", product_text, height=200)
    
    unsafe_ingredients = check_safety(product_text, user_conditions)
    
    if unsafe_ingredients:
        st.subheader("🚨 Unsafe Ingredients Detected!")
        for idx, (ingredient, effect) in enumerate(unsafe_ingredients, start=1):
            definition = fetch_wikipedia_definition(ingredient)
            st.write(f"{idx}. **{ingredient.capitalize()}**: {effect}\n{definition}")
    else:
        st.success("✅ The product is safe based on the provided conditions!")