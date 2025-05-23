# automated_skeptic_mvp/data/sample_claims.py
"""
Sample test claims for MVP development and testing
"""

# Tier 1 claims for MVP testing
SAMPLE_CLAIMS = [
    # Historical dates
    "The Berlin Wall fell in 1989.",
    "World War II ended in 1945.",
    "The first moon landing occurred in 1969.",
    "The Titanic sank in 1912.",
    "The Great Wall of China was built during the Ming Dynasty.",
    
    # Biographical facts
    "Albert Einstein was born in Germany.",
    "Elon Musk was born in South Africa.",
    "Leonardo da Vinci painted the Mona Lisa.",
    "Barack Obama was the 44th President of the United States.",
    "Marie Curie won two Nobel Prizes.",
    
    # Corporate facts
    "Apple was founded in 1976.",
    "Microsoft was founded by Bill Gates and Paul Allen.",
    "Google was founded by Larry Page and Sergey Brin.",
    "Amazon started as an online bookstore.",
    "Tesla was founded by Elon Musk.",
    
    # Recent news events
    "The 2024 Olympics were held in Paris.",
    "The COVID-19 pandemic began in 2019.",
    "SpaceX successfully launched astronauts to the International Space Station.",
    "The iPhone was first released in 2007.",
    "Facebook changed its name to Meta in 2021.",
    
    # Test claims with potential for contradiction
    "The Earth is flat.",
    "Vaccines cause autism.",
    "Climate change is not real.",
    "The Holocaust never happened.",
    "Elvis Presley is still alive.",
]

def get_test_claims(count: int = 25) -> list:
    """Get a subset of test claims for development"""
    return SAMPLE_CLAIMS[:count]

def save_test_claims_csv(filename: str = "data/test_claims.csv"):
    """Save test claims to CSV file"""
    import csv
    import os
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['claim', 'expected_category', 'notes'])
        
        for claim in SAMPLE_CLAIMS:
            # Simple categorization based on content
            if any(year in claim for year in ['1989', '1945', '1969', '1912']):
                category = 'historical_date'
            elif any(name in claim for name in ['Einstein', 'Musk', 'da Vinci', 'Obama', 'Curie']):
                category = 'biographical_fact'
            elif any(company in claim for company in ['Apple', 'Microsoft', 'Google', 'Amazon', 'Tesla']):
                category = 'corporate_fact'
            elif any(event in claim for event in ['Olympics', 'COVID', 'SpaceX', 'iPhone', 'Facebook']):
                category = 'news_event'
            else:
                category = 'unknown'
            
            writer.writerow([claim, category, ''])

if __name__ == "__main__":
    # Generate test claims CSV when run directly
    save_test_claims_csv()
    print(f"Generated {len(SAMPLE_CLAIMS)} test claims in data/test_claims.csv")
