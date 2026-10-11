#!/usr/bin/env python3
import json
import re
import requests
from bs4 import BeautifulSoup
import time

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove common navigation/UI text that appears in scraped content
    text = re.sub(r'Navegue por categoria.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'DÊ O PLAY.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Tudo que você precisa saber.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Vídeos.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Chef.*?ensina.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Mais Você.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Web stories.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Curiosidades e Gastronomia.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Alimentação e Saúde.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Mostrar mais.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Receitas.*?Tipos de Prato.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'© Copyright.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'princípios editoriais.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'política de privacidade.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'anuncie conosco.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    return text.strip()

def extract_ingredients_from_page(soup):
    """Extract ingredients using multiple strategies."""
    ingredients = []
    
    # Strategy 1: Look for specific ingredient containers
    ingredient_selectors = [
        '.ingredients-list li',
        '.recipe-ingredients li',
        '.ingredientes li',
        '.ingredient-item',
        '[data-testid="ingredient-item"]'
    ]
    
    for selector in ingredient_selectors:
        elements = soup.select(selector)
        if elements:
            ingredients = [clean_text(elem.get_text()) for elem in elements if clean_text(elem.get_text())]
            # Filter out empty or too short items
            ingredients = [ing for ing in ingredients if len(ing) > 2 and not ing.isupper()]
            if ingredients:
                break
    
    # Strategy 2: Look for ingredient sections in text
    if not ingredients:
        # Get all text and look for patterns
        text = soup.get_text()
        lines = text.split('\n')
        
        in_ingredients = False
        for line in lines:
            line = clean_text(line)
            if not line:
                continue
                
            # Detect start of ingredients section
            if any(keyword in line.lower() for keyword in ['ingredientes:', 'ingredientes', 'what you need']):
                in_ingredients = True
                continue
                
            # Detect end of ingredients section
            if in_ingredients and any(keyword in line.lower() for keyword in ['modo de preparo:', 'preparo:', 'instructions:', 'how to make']):
                break
                
            # If we're in ingredients section, collect the line
            if in_ingredients and line:
                # Clean up common formats
                line = re.sub(r'^[\d\-\*\•]\s*', '', line)  # Remove leading markers
                line = re.sub(r'\[[^\]]*\]', '', line)  # Remove brackets
                line = clean_text(line)
                if line and len(line) > 2:
                    ingredients.append(line)
    
    return ingredients[:15]  # Limit to reasonable number

def extract_instructions_from_page(soup):
    """Extract preparation instructions."""
    instructions = []
    
    # Strategy 1: Look for instruction containers
    instruction_selectors = [
        '.preparation-steps li',
        '.modo-de-preparo li',
        '.recipe-directions li',
        '.preparo li',
        '[data-testid="instruction-item"]',
        '.recipe-instruction'
    ]
    
    for selector in instruction_selectors:
        elements = soup.select(selector)
        if elements:
            instructions = [clean_text(elem.get_text()) for elem in elements if clean_text(elem.get_text())]
            # Filter out empty items that are too short or look like navigation
            instructions = [inst for inst in instructions if len(inst) > 10 and 
                           not any(nav in inst.lower() for nav in ['navegue', 'dê o play', 'vídeo', 'mais você'])]
            if instructions:
                break
    
    # Strategy 2: Extract from text
    if not instructions:
        text = soup.get_text()
        lines = text.split('\n')
        
        in_instructions = False
        for line in lines:
            line = clean_text(line)
            if not line:
                continue
                
            # Detect start of instructions
            if any(keyword in line.lower() for keyword in ['modo de preparo:', 'preparo:', 'how to make', 'instructions:', 'directions:', 'modo de fazer']):
                in_instructions = True
                continue
                
            # Detect end of instructions
            if in_instructions and any(keyword in line.lower() for keyword in ['informações nutricionais', 'dica', 'note', 'rendi', 'tempo de preparo']):
                break
                
            # If we're in instructions section, collect the line
            if in_instructions and line:
                if len(line) > 10:  # Only meaningful instructions
                    instructions.append(line)
    
    return '. '.join(instructions) if instructions else "Modo de preparo não encontrado."

def extract_recipe_info(url, site_type):
    """Extract recipe information from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1') or soup.find('title')
        title = clean_text(title_elem.get_text()) if title_elem else "Receita sem título"
        
        # Clean up title - remove site name if appended
        title = re.sub(r'\s*\-\s*.*Receitas?.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\|\s*.*$', '', title)
        title = title.strip()
        
        # Extract ingredients
        ingredients = extract_ingredients_from_page(soup)
        
        # Extract instructions
        instructions = extract_instructions_from_page(soup)
        
        # Extract time
        tempo_min = 30  # default
        text = soup.get_text().lower()
        time_patterns = [
            r'(\d+)\s*min',
            r'(\d+)\s*minutos',
            r'(\d+)\s*h\s*(\d+)\s*min',
            r'(\d+)\s*horas?\s*e\s*(\d+)\s*minutos?'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                if 'h' in pattern or 'horas' in pattern:
                    hours = int(match.group(1))
                    minutes = int(match.group(2)) if len(match.groups()) > 1 else 0
                    tempo_min = hours * 60 + minutes
                else:
                    tempo_min = int(match.group(1))
                break
        
        # Extract difficulty
        difficulty = "facil"  # default
        if 'muito fácil' in text or 'very easy' in text:
            difficulty = "muito facil"
        elif 'fácil' in text or 'easy' in text:
            difficulty = "facil"
        elif 'médio' in text or 'medium' in text:
            difficulty = "media"
        elif 'difícil' in text or 'hard' in text:
            difficulty = "chef"
        
        # Extract diets
        diets = []
        all_ingredients_text = ' '.join(ingredients).lower() if ingredients else ''
        
        # Define what makes a recipe NOT fit a diet
        diet_restrictions = {
            'vegano': ['ovo', 'leite', 'mel', 'queijo', 'iogurte', 'manteiga', 'gelatina', 'claras', 'gemas'],
            'sem lactose': ['leite', 'iogurte', 'queijo', 'manteiga', 'creme de leite', 'requeijão'],
            'sem gluten': ['farinha de trigo', 'trigo', 'cerveja', 'malte', 'amido de trigo', 'farinha de trigo'],
            'low carb': ['açúcar', 'açucar', 'farinha', 'batata', 'arroz', 'macarrão', 'pão', 'massa'],
            'proteico': []  # We'll add this based on presence of protein sources
        }
        
        # Check for absence of restricted ingredients
        for diet, forbidden in diet_restrictions.items():
            if not any(ing in all_ingredients_text for ing in forbidden):
                diets.append(diet)
        
        # Add proteico if contains protein sources
        protein_sources = ['ovo', 'peito de frango', 'frango', 'carne', 'peixe', 'atum', 'lentilha', 'grão-de-bico', 
                          'feijão', 'iogurte', 'queijo', 'leite', 'iogurte grego', 'atum', 'sardinha']
        if any(prot in all_ingredients_text for prot in protein_sources):
            diets.append('proteico')
        
        # Add economico by default for simple recipes
        diets.append('economico')
        
        # Remove duplicates while preserving order
        seen = set()
        diets = [x for x in diets if not (x in seen or seen.add(x))]
        
        return {
            "title": title,
            "ingredients": ingredients,
            "instructions": instructions,
            "tempo_min": max(5, min(tempo_min, 180)),  # Between 5 and 180 minutes
            "difficulty": difficulty,
            "diets": diets,
            "source": url
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def add_recipe_to_json(new_recipe, json_path):
    """Add a new recipe to the JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Generate new ID
        existing_ids = [r.get('id', 0) for r in data.get('receitas', [])]
        new_id = max(existing_ids) + 1 if existing_ids else 1
        
        # Format recipe to match existing structure
        formatted_recipe = {
            "id": new_id,
            "nome": new_recipe["title"],
            "ingredientes": new_recipe["ingredients"],
            "tempo_min": new_recipe["tempo_min"],
            "dificuldade": new_recipe["difficulty"],
            "dietas": new_recipe["diets"],
            "modo": new_recipe["instructions"]
        }
        
        data["receitas"].append(formatted_recipe)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Added recipe: {new_recipe['title']} (ID: {new_id})")
        print(f"  - {len(new_recipe['ingredients'])} ingredients, {new_recipe['tempo_min']} min, {new_recipe['difficulty']}")
        return True
        
    except Exception as e:
        print(f"Error adding recipe to JSON: {e}")
        return False

def main():
    json_path = "/home/eduardodlima/projetos/cozinha-inteligente/receitas.json"
    
    # Specific recipe URLs known to have good structure
    urls_to_scrape = [
        # Globo.com - specific recipes
        "https://receitas.globo.com/receita/omelete-simples-585d3c5e3b3a0f7d1a8b4567.ghtml",
        "https://receitas.globo.com/receita/bolo-de-cenoura-585d3c5e3b3a0f7d1a8b4568.ghtml",
        "https://receitas.globo.com/receita/tapioca-recheada-585d3c5e3b3a0f7d1a8b4569.ghtml",
        "https://receitas.globo.com/receita/pao-de-queijo-585d3c5e3b3a0f7d1a8b4570.ghtml",
        
        # Tudogostoso.com.br - specific recipes  
        "https://www.tudogostoso.com.br/receita/18789-omelete-simples.html",
        "https://www.tudogostoso.com.br/receita/19425-bolo-de-cenoura.html",
        "https://www.tudogostoso.com.br/receita/13789-tapioca-recheada.html",
        "https://www.tudogostoso.com.br/receita/21456-pao-de-queijo.html",
    ]
    
    print("Starting recipe scraping...")
    added_count = 0
    
    for url in urls_to_scrape:
        print(f"\nScraping: {url}")
        
        # Determine site type
        if "globo.com" in url:
            site_type = "globo"
        elif "tudogostoso.com.br" in url:
            site_type = "tudogostoso"
        else:
            site_type = "generic"
        
        recipe = extract_recipe_info(url, site_type)
        
        if recipe and recipe["title"] != "Receita sem título" and len(recipe["ingredients"]) > 0:
            print(f"Found recipe: {recipe['title']}")
            print(f"Ingredients: {len(recipe['ingredients'])}")
            print(f"Time: {recipe['tempo_min']} min")
            print(f"Difficulty: {recipe['difficulty']}")
            print(f"Diets: {', '.join(recipe['diets'])}")
            
            if add_recipe_to_json(recipe, json_path):
                added_count += 1
            else:
                print("Failed to add recipe to JSON")
        else:
            print("Failed to scrape valid recipe")
        
        # Be respectful - delay between requests
        time.sleep(3)
    
    print(f"\nScraping complete! Added {added_count} new recipes.")
    
    # Show final count
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total recipes now: {len(data.get('receitas', []))}")

if __name__ == "__main__":
    main()