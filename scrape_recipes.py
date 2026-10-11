#!/usr/bin/env python3
import json
import re
import requests
from bs4 import BeautifulSoup
import time

def normalize_text(text):
    """Normalize text by removing extra whitespace and special characters."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def extract_ingredients_from_text(text):
    """Extract ingredients from text using common patterns."""
    # Look for common ingredient patterns
    lines = text.split('\n')
    ingredients = []
    
    in_ingredients_section = False
    for line in lines:
        line = normalize_text(line)
        if not line:
            continue
            
        # Check if we're entering an ingredients section
        if any(keyword in line.lower() for keyword in ['ingredientes:', 'ingredientes', 'what you need', 'you\'ll need']):
            in_ingredients_section = True
            continue
            
        # Check if we're leaving the ingredients section
        if in_ingredients_section and any(keyword in line.lower() for keyword in ['modo de preparo:', 'preparo:', 'instructions:', 'directions:', 'how to make']):
            break
            
        # If we're in ingredients section, collect the line
        if in_ingredients_section and line:
            # Clean up common ingredient formats
            line = re.sub(r'^[\d\-\*\•\•]\s*', '', line)  # Remove leading numbers/bullets
            line = re.sub(r'\[[^\]]*\]', '', line)  # Remove text in brackets
            line = normalize_text(line)
            if line and len(line) > 2 and not line.isupper():  # Avoid section headers
                ingredients.append(line)
    
    return ingredients

def scrape_globo_recipe(url):
    """Scrape a recipe from Globo.com."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find title
        title_elem = soup.find('h1') or soup.find('title')
        title = normalize_text(title_elem.get_text()) if title_elem else "Receita sem título"
        
        # Try to find ingredients - look for common patterns
        ingredients = []
        
        # Look for ingredients in specific containers
        ingredient_selectors = [
            '.ingredients-list li',
            '.recipe-ingredients li',
            '.ingredientes li',
            '[data-testid="ingredient-item"]',
            '.recipe-ingredient'
        ]
        
        for selector in ingredient_selectors:
            elements = soup.select(selector)
            if elements:
                ingredients = [normalize_text(elem.get_text()) for elem in elements if normalize_text(elem.get_text())]
                break
        
        # If no ingredients found with selectors, try to extract from text
        if not ingredients:
            # Get all text and try to extract ingredients
            text = soup.get_text()
            ingredients = extract_ingredients_from_text(text)
        
        # Try to find preparation instructions
        instructions = ""
        instruction_selectors = [
            '.preparation-steps li',
            '.modo-de-preparo li',
            '.recipe-directions li',
            '[data-testid="instruction-item"]',
            '.recipe-instruction'
        ]
        
        for selector in instruction_selectors:
            elements = soup.select(selector)
            if elements:
                instructions = '. '.join([normalize_text(elem.get_text()) for elem in elements if normalize_text(elem.get_text())])
                break
        
        # If no instructions found with selectors, try to extract from text
        if not instructions:
            text = soup.get_text()
            # Look for preparation section
            lines = text.split('\n')
            in_prep = False
            prep_lines = []
            for line in lines:
                line = normalize_text(line)
                if any(keyword in line.lower() for keyword in ['modo de preparo:', 'preparo:', 'instructions:', 'directions:', 'how to make', 'modo de fazer']):
                    in_prep = True
                    continue
                if in_prep and line:
                    # Stop if we hit another section
                    if any(keyword in line.lower() for keyword in ['informações nutricionais', 'dica', 'note', 'rendi']):
                        break
                    prep_lines.append(line)
            if prep_lines:
                instructions = '. '.join(prep_lines)
        
        # Determine difficulty based on time or text
        difficulty = "facil"  # default
        time_text = soup.get_text().lower()
        if 'fácil' in time_text or 'muito fácil' in time_text or 'very easy' in time_text:
            if 'muito fácil' in time_text or 'very easy' in time_text:
                difficulty = "muito facil"
            else:
                difficulty = "facil"
        elif 'médio' in time_text or 'medium' in time_text:
            difficulty = "media"
        elif 'difícil' in time_text or 'hard' in time_text or 'chef' in time_text:
            difficulty = "chef"
        
        # Estimate time (look for time patterns)
        tempo_min = 30  # default
        time_patterns = [
            r'(\d+)\s*min',
            r'(\d+)\s*minutos',
            r'(\d+)\s*h\s*(\d+)\s*min',
            r'(\d+)\s*horas?\s*e\s*(\d+)\s*minutos?'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, time_text)
            if match:
                if 'h' in pattern or 'horas' in pattern:
                    hours = int(match.group(1))
                    minutes = int(match.group(2)) if len(match.groups()) > 1 else 0
                    tempo_min = hours * 60 + minutes
                else:
                    tempo_min = int(match.group(1))
                break
        
        # Determine diets based on ingredients
        diets = []
        all_ingredients_text = ' '.join(ingredients).lower() if ingredients else ''
        
        diet_keywords = {
            'vegano': ['ovo', 'leite', 'mel', 'queijo', 'iogurte', 'manteiga', 'gelatina', 'mel'],
            'sem lactose': ['leite', 'iogurte', 'queijo', 'manteiga', 'creme de leite'],
            'sem gluten': ['farinha de trigo', 'trigo', 'cerveja', 'malte', 'amido de trigo'],
            'low carb': ['açúcar', 'açucar', 'farinha', 'batata', 'arroz', 'macarrão', 'pão'],
            'proteico': ['ovo', 'peito de frango', 'carne', 'peixe', 'atum', 'frango', 'carne moída', 'lentilha', 'grão-de-bico'],
            'economico': []  # Assume economic by default for simple recipes
        }
        
        # Check for absence of ingredients to determine diets
        for diet, forbidden in diet_keywords.items():
            if diet != 'economico':  # Skip economic for now
                if not any(ing in all_ingredients_text for ing in forbidden):
                    diets.append(diet)
        
        # Add economic diet by default for simple recipes
        diets.append('economico')
        
        # Remove duplicates
        diets = list(dict.fromkeys(diets))
        
        return {
            "title": title,
            "ingredients": ingredients[:20],  # Limit to 20 ingredients
            "instructions": instructions[:500] if instructions else "Modo de preparo não encontrado.",
            "tempo_min": max(5, min(tempo_min, 180)),  # Between 5 and 180 minutes
            "difficulty": difficulty,
            "diets": diets,
            "source": url
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_tudogostoso_recipe(url):
    """Scrape a recipe from Tudogostoso.com.br."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find title
        title_elem = soup.find('h1') or soup.find('title')
        title = normalize_text(title_elem.get_text()) if title_elem else "Receita sem título"
        
        # Tudogostoso specific selectors
        ingredients = []
        ingredient_selectors = [
            '.ingredients-list li',
            '.recipe-ingredients li',
            '.ingrediente',
            '.ingredient-item'
        ]
        
        for selector in ingredient_selectors:
            elements = soup.select(selector)
            if elements:
                ingredients = [normalize_text(elem.get_text()) for elem in elements if normalize_text(elem.get_text())]
                break
        
        # If no ingredients found, try text extraction
        if not ingredients:
            text = soup.get_text()
            ingredients = extract_ingredients_from_text(text)
        
        # Instructions
        instructions = ""
        instruction_selectors = [
            '.preparation-mode li',
            '.modo-de-preparo li',
            '.recipe-directions li',
            '.preparo li'
        ]
        
        for selector in instruction_selectors:
            elements = soup.select(selector)
            if elements:
                instructions = '. '.join([normalize_text(elem.get_text()) for elem in elements if normalize_text(elem.get_text())])
                break
        
        if not instructions:
            text = soup.get_text()
            lines = text.split('\n')
            in_prep = False
            prep_lines = []
            for line in lines:
                line = normalize_text(line)
                if any(keyword in line.lower() for keyword in ['modo de preparo:', 'preparo:', 'como fazer', 'modo de fazer']):
                    in_prep = True
                    continue
                if in_prep and line:
                    if any(keyword in line.lower() for keyword in ['informações', 'dica', 'note', 'rendi', 'tempo de preparo']):
                        break
                    prep_lines.append(line)
            if prep_lines:
                instructions = '. '.join(prep_lines)
        
        # Difficulty
        difficulty = "facil"
        time_text = soup.get_text().lower()
        if 'muito fácil' in time_text or 'very easy' in time_text:
            difficulty = "muito facil"
        elif 'fácil' in time_text or 'easy' in time_text:
            difficulty = "facil"
        elif 'médio' in time_text or 'medium' in time_text:
            difficulty = "media"
        elif 'difícil' in time_text or 'hard' in time_text:
            difficulty = "chef"
        
        # Time
        tempo_min = 30
        time_patterns = [
            r'(\d+)\s*min',
            r'(\d+)\s*minutos',
            r'(\d+)\s*h\s*(\d+)\s*min',
            r'(\d+)\s*horas?\s*e\s*(\d+)\s*minutos?'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, time_text)
            if match:
                if 'h' in pattern or 'horas' in pattern:
                    hours = int(match.group(1))
                    minutes = int(match.group(2)) if len(match.groups()) > 1 else 0
                    tempo_min = hours * 60 + minutes
                else:
                    tempo_min = int(match.group(1))
                break
        
        # Diets
        diets = []
        all_ingredients_text = ' '.join(ingredients).lower() if ingredients else ''
        
        diet_keywords = {
            'vegano': ['ovo', 'leite', 'mel', 'queijo', 'iogurte', 'manteiga', 'gelatina'],
            'sem lactose': ['leite', 'iogurte', 'queijo', 'manteiga', 'creme de leite'],
            'sem gluten': ['farinha de trigo', 'trigo', 'cerveja', 'malte', 'amido de trigo'],
            'low carb': ['açúcar', 'açucar', 'farinha', 'batata', 'arroz', 'macarrão', 'pão'],
            'proteico': ['ovo', 'peito de frango', 'carne', 'peixe', 'atum', 'frango', 'carne moída', 'lentilha', 'grão-de-bico'],
            'economico': []
        }
        
        for diet, forbidden in diet_keywords.items():
            if diet != 'economico':
                if not any(ing in all_ingredients_text for ing in forbidden):
                    diets.append(diet)
        
        diets.append('economico')
        diets = list(dict.fromkeys(diets))
        
        return {
            "title": title,
            "ingredients": ingredients[:20],
            "instructions": instructions[:500] if instructions else "Modo de preparo não encontrado.",
            "tempo_min": max(5, min(tempo_min, 180)),
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
        return True
        
    except Exception as e:
        print(f"Error adding recipe to JSON: {e}")
        return False

def main():
    json_path = "/home/eduardodlima/projetos/cozinha-inteligente/receitas.json"
    
    # URLs to scrape (these are examples - in practice we'd search for more)
    urls_to_scrape = [
        # Globo.com recipes
        "https://receitas.globo.com/omelete-delicioso-50fed6c34d38852e5500004c.ghtml",
        "https://receitas.globo.com/tipos-de-prato/acompanhamentos/omelete-519fe6194d38852ebc000046.ghtml",
        "https://receitas.globo.com/tipos-de-prato/bolos/bolo-de-cenoura-de-liquidificador-4e80cb6a8811965be7003c43.ghtml",
        # Tudogostoso.com.br recipes
        "https://www.tudogostoso.com.br/receita/23-bolo-de-cenoura.html",
        "https://www.tudogostoso.com.br/receita/24580-bolo-de-cenoura-simples.html",
    ]
    
    print("Starting recipe scraping...")
    added_count = 0
    
    for url in urls_to_scrape:
        print(f"\nScraping: {url}")
        
        if "globo.com" in url:
            recipe = scrape_globo_recipe(url)
        elif "tudogostoso.com.br" in url:
            recipe = scrape_tudogostoso_recipe(url)
        else:
            print(f"Unknown site for URL: {url}")
            continue
        
        if recipe:
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
            print("Failed to scrape recipe")
        
        # Be respectful - delay between requests
        time.sleep(2)
    
    print(f"\nScraping complete! Added {added_count} new recipes.")
    
    # Show final count
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total recipes now: {len(data.get('receitas', []))}")

if __name__ == "__main__":
    main()