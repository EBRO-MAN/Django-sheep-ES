from django.core.exceptions import ValidationError
from datetime import datetime
from django.db.models import Q
from .models import Sheep, BreedingCycle

def get_available_rams():
    """Get all healthy rams available for breeding"""
    return Sheep.objects.filter(
        sex='MALE', 
        is_healthy=True,
        type__in=['RAM', 'YOUNG_RAM']
    ).select_related('parent_ewe', 'parent_ram')

def get_available_ewes():
    """Get all healthy ewes available for breeding"""
    return Sheep.objects.filter(
        sex='FEMALE',
        is_healthy=True,
        type__in=['EWE', 'GIMMER']
    ).select_related('parent_ewe', 'parent_ram')

def check_breed_compatibility(ram, ewe):
    """
    Check if ram and ewe breeds are compatible based on registration rules
    Returns True if compatible, False if not
    """
    ram_breed = ram.breed
    ewe_breed = ewe.breed
    
    # Breed compatibility rules from SSD section 3.1
    # RAM restrictions (what ewes they can mate with)
    ram_restrictions = {
        'PA': ['LOCAL', 'PA', 'AC'],    # PA rams can mate with LOCAL, PA, AC ewes
        'PD': ['LOCAL', 'PD', 'DC'],    # PD rams can mate with LOCAL, PD, DC ewes  
        'LOCAL': ['LOCAL'],             # LOCAL rams can only mate with LOCAL ewes
        'AC': ['PA'],                   # AC rams follow PA rules
        'DC': ['PD']                    # DC rams follow PD rules
    }
    
    # EWE restrictions (what rams they can mate with)
    ewe_restrictions = {
        'AC': ['PA'],                   # AC ewes can only mate with PA rams
        'DC': ['PD'],                   # DC ewes can only mate with PD rams
        # LOCAL, PA, PD ewes have no restrictions on which rams they can mate with
        # Their compatibility is determined by the ram's restrictions
    }
    
    # Check ram restrictions
    if ram_breed in ram_restrictions:
        allowed_ewe_breeds = ram_restrictions[ram_breed]
        if ewe_breed not in allowed_ewe_breeds:
            return False
    
    # Check ewe restrictions (only for breeds that have specific requirements)
    if ewe_breed in ewe_restrictions:
        allowed_ram_breeds = ewe_restrictions[ewe_breed]
        if ram_breed not in allowed_ram_breeds:
            return False
    
    return True

def predict_lamb_breed(ewe, ram):
    """
    Predict lamb breed and breed level based on parent combinations
    Returns: (breed, breed_level) or (None, None) for manual input
    """
    ewe_breed = ewe.breed
    ram_breed = ram.breed
    ewe_level = ewe.breed_level
    ram_level = ram.breed_level
    
    # Breed prediction rules from SSD section 3.1
    breed_prediction_rules = {
        ('LOCAL', 'LOCAL'): ('LOCAL', 100.0),
        ('PA', 'LOCAL'): ('AC', 50.0),
        ('PD', 'LOCAL'): ('DC', 50.0),
        ('AC', 'PA'): ('AC', (ewe_level + ram_level) / 2),
        ('DC', 'PD'): ('DC', (ewe_level + ram_level) / 2),
        ('PA', 'PA'): ('PA', 100.0),
        ('PD', 'PD'): ('PD', 100.0),
    }
    
    # Try both orderings since rules might be directional
    if (ewe_breed, ram_breed) in breed_prediction_rules:
        return breed_prediction_rules[(ewe_breed, ram_breed)]
    elif (ram_breed, ewe_breed) in breed_prediction_rules:
        return breed_prediction_rules[(ram_breed, ewe_breed)]
    
    return None, None  # Manual input required

def get_compatible_ewes(selected_ram):
    """
    Filter ewes that are compatible based on both breed rules and family relationships
    """
    all_ewes = get_available_ewes()
    compatible_ewes = []
    
    for ewe in all_ewes:
        # Check breed compatibility first (faster check)
        if not check_breed_compatibility(selected_ram, ewe):
            continue
        
        # Then check inbreeding prevention
        if check_for_inbreeding(ewe, selected_ram):
            compatible_ewes.append(ewe)
    
    return compatible_ewes

def get_breed_restrictions(ram):
    """
    Get the breed restrictions for a specific ram
    Returns a list of allowed ewe breeds
    """
    breed_restrictions = {
        'PA': ['LOCAL', 'PA', 'AC'],
        'PD': ['LOCAL', 'PD', 'DC'], 
        'LOCAL': ['LOCAL'],
        'AC': ['PA'],  # AC rams follow PA rules
        'DC': ['PD']   # DC rams follow PD rules
    }
    
    return breed_restrictions.get(ram.breed, [])

def get_breed_compatibility_info(ram):
    """
    Get detailed breed compatibility information for display
    """
    restrictions = get_breed_restrictions(ram)
    
    compatibility_info = {
        'ram_breed': ram.breed,
        'allowed_ewe_breeds': restrictions,
        'restriction_description': get_restriction_description(ram.breed),
        'example_pairings': get_example_pairings(ram.breed)
    }
    
    return compatibility_info

def get_restriction_description(ram_breed):
    """
    Get a human-readable description of breed restrictions
    """
    descriptions = {
        'PA': "PA rams can breed with Local, PA, and AC ewes to produce AC lambs (50%) or PA lambs (100%)",
        'PD': "PD rams can breed with Local, PD, and DC ewes to produce DC lambs (50%) or PD lambs (100%)",
        'LOCAL': "Local rams can only breed with Local ewes to produce Local lambs (100%)",
        'AC': "AC rams follow the same rules as PA rams",
        'DC': "DC rams follow the same rules as PD rams"
    }
    
    return descriptions.get(ram_breed, "No specific breed restrictions")

def get_example_pairings(ram_breed):
    """
    Get example breed pairings and their outcomes
    """
    examples = {
        'PA': [
            {'ewe': 'LOCAL', 'lamb': 'AC', 'level': '50%'},
            {'ewe': 'PA', 'lamb': 'PA', 'level': '100%'},
            {'ewe': 'AC', 'lamb': 'AC', 'level': 'Average of parents'}
        ],
        'PD': [
            {'ewe': 'LOCAL', 'lamb': 'DC', 'level': '50%'},
            {'ewe': 'PD', 'lamb': 'PD', 'level': '100%'},
            {'ewe': 'DC', 'lamb': 'DC', 'level': 'Average of parents'}
        ],
        'LOCAL': [
            {'ewe': 'LOCAL', 'lamb': 'LOCAL', 'level': '100%'}
        ]
    }
    
    return examples.get(ram_breed, [])

# ... (keep all the existing family relationship functions the same)
def get_all_siblings(sheep, include_half_siblings=True):
    """Get all siblings (full and half) of a sheep"""
    if not sheep:
        return Sheep.objects.none()
    
    siblings = Sheep.objects.none()
    
    # Full siblings (same both parents)
    if sheep.parent_ewe and sheep.parent_ram:
        siblings = Sheep.objects.filter(
            parent_ewe=sheep.parent_ewe,
            parent_ram=sheep.parent_ram
        ).exclude(ear_tag_number=sheep.ear_tag_number)
    
    if include_half_siblings:
        # Half-siblings (same mother, different father)
        if sheep.parent_ewe:
            half_sibs_mother = Sheep.objects.filter(
                parent_ewe=sheep.parent_ewe
            ).exclude(
                Q(parent_ram=sheep.parent_ram) | Q(ear_tag_number=sheep.ear_tag_number)
            )
            siblings = siblings.union(half_sibs_mother)
        
        # Half-siblings (same father, different mother)
        if sheep.parent_ram:
            half_sibs_father = Sheep.objects.filter(
                parent_ram=sheep.parent_ram
            ).exclude(
                Q(parent_ewe=sheep.parent_ewe) | Q(ear_tag_number=sheep.ear_tag_number)
            )
            siblings = siblings.union(half_sibs_father)
    
    return siblings

def get_nieces_and_nephews(sheep):
    """Get all nieces and nephews of a sheep (children of siblings)"""
    nieces_nephews = Sheep.objects.none()
    siblings = get_all_siblings(sheep, include_half_siblings=True)
    
    for sibling in siblings:
        # Get all children of each sibling
        children = Sheep.objects.filter(
            Q(parent_ewe=sibling) | Q(parent_ram=sibling)
        )
        nieces_nephews = nieces_nephews.union(children)
    
    return nieces_nephews

def get_uncles_and_aunts(sheep):
    """Get all uncles and aunts of a sheep (siblings of parents)"""
    uncles_aunts = Sheep.objects.none()
    
    # Mother's siblings
    if sheep.parent_ewe:
        mother_siblings = get_all_siblings(sheep.parent_ewe, include_half_siblings=True)
        uncles_aunts = uncles_aunts.union(mother_siblings)
    
    # Father's siblings
    if sheep.parent_ram:
        father_siblings = get_all_siblings(sheep.parent_ram, include_half_siblings=True)
        uncles_aunts = uncles_aunts.union(father_siblings)
    
    return uncles_aunts

def check_for_inbreeding(ewe, ram):
    """
    Comprehensive inbreeding prevention check
    Returns True if breeding is allowed, False if prohibited
    """
    # Direct parent-child relationships
    if ram == ewe.parent_ram:
        return False  # Father-daughter
    if ewe == ram.parent_ewe:
        return False  # Mother-son
    
    # Full siblings (same both parents)
    if (ewe.parent_ewe and ram.parent_ewe and 
        ewe.parent_ewe == ram.parent_ewe and 
        ewe.parent_ram == ram.parent_ram):
        return False
    
    # Half-siblings (same father, different mother)
    if (ewe.parent_ram and ram.parent_ram and 
        ewe.parent_ram == ram.parent_ram and 
        ewe.parent_ewe != ram.parent_ewe):
        return False
    
    # Half-siblings (same mother, different father)
    if (ewe.parent_ewe and ram.parent_ewe and 
        ewe.parent_ewe == ram.parent_ewe and 
        ewe.parent_ram != ram.parent_ram):
        return False
    
    # Uncle/niece relationships
    ewe_uncles_aunts = get_uncles_and_aunts(ewe)
    if ram in ewe_uncles_aunts:
        return False
    
    # Aunt/nephew relationships
    ram_uncles_aunts = get_uncles_and_aunts(ram)
    if ewe in ram_uncles_aunts:
        return False
    
    # Grandparent relationships
    grandparents = set()
    if ewe.parent_ewe:
        grandparents.add(ewe.parent_ewe.parent_ewe)
        grandparents.add(ewe.parent_ewe.parent_ram)
    if ewe.parent_ram:
        grandparents.add(ewe.parent_ram.parent_ewe)
        grandparents.add(ewe.parent_ram.parent_ram)
    grandparents = {gp for gp in grandparents if gp}
    if ram in grandparents:
        return False
    
    # Ram's grandparents
    ram_grandparents = set()
    if ram.parent_ewe:
        ram_grandparents.add(ram.parent_ewe.parent_ewe)
        ram_grandparents.add(ram.parent_ewe.parent_ram)
    if ram.parent_ram:
        ram_grandparents.add(ram.parent_ram.parent_ewe)
        ram_grandparents.add(ram.parent_ram.parent_ram)
    ram_grandparents = {gp for gp in ram_grandparents if gp}
    if ewe in ram_grandparents:
        return False
    
    # First cousins
    if are_first_cousins(ewe, ram):
        return False
    
    # Niece/nephew relationships
    ram_nieces_nephews = get_nieces_and_nephews(ram)
    if ewe in ram_nieces_nephews:
        return False
    
    ewe_nieces_nephews = get_nieces_and_nephews(ewe)
    if ram in ewe_nieces_nephews:
        return False
    
    return True  # No inbreeding detected

def are_first_cousins(ewe, ram):
    """Check if two sheep are first cousins"""
    ewe_grandparents = set()
    ram_grandparents = set()
    
    # Ewe's grandparents
    if ewe.parent_ewe:
        ewe_grandparents.add(ewe.parent_ewe.parent_ewe)
        ewe_grandparents.add(ewe.parent_ewe.parent_ram)
    if ewe.parent_ram:
        ewe_grandparents.add(ewe.parent_ram.parent_ewe)
        ewe_grandparents.add(ewe.parent_ram.parent_ram)
    
    # Ram's grandparents
    if ram.parent_ewe:
        ram_grandparents.add(ram.parent_ewe.parent_ewe)
        ram_grandparents.add(ram.parent_ewe.parent_ram)
    if ram.parent_ram:
        ram_grandparents.add(ram.parent_ram.parent_ewe)
        ram_grandparents.add(ram.parent_ram.parent_ram)
    
    # Remove None values
    ewe_grandparents = {gp for gp in ewe_grandparents if gp}
    ram_grandparents = {gp for gp in ram_grandparents if gp}
    
    # If they share any grandparents, they are cousins
    return bool(ewe_grandparents.intersection(ram_grandparents))

def get_family_relationship(ewe, ram):
    """Helper function to determine the specific family relationship"""
    relationships = []
    
    # Direct parent-child
    if ram == ewe.parent_ram:
        relationships.append("Father-Daughter")
    if ewe == ram.parent_ewe:
        relationships.append("Mother-Son")
    
    # Siblings
    if (ewe.parent_ewe and ram.parent_ewe and 
        ewe.parent_ewe == ram.parent_ewe and 
        ewe.parent_ram == ram.parent_ram):
        relationships.append("Full Siblings")
    
    # Half-siblings
    if (ewe.parent_ram and ram.parent_ram and 
        ewe.parent_ram == ram.parent_ram and 
        ewe.parent_ewe != ram.parent_ewe):
        relationships.append("Half-Siblings (Same Father)")
    
    if (ewe.parent_ewe and ram.parent_ewe and 
        ewe.parent_ewe == ram.parent_ewe and 
        ewe.parent_ram != ram.parent_ram):
        relationships.append("Half-Siblings (Same Mother)")
    
    # Uncle/niece
    ewe_uncles_aunts = get_uncles_and_aunts(ewe)
    if ram in ewe_uncles_aunts:
        relationships.append("Uncle-Niece")
    
    # Aunt/nephew
    ram_uncles_aunts = get_uncles_and_aunts(ram)
    if ewe in ram_uncles_aunts:
        relationships.append("Aunt-Nephew")
    
    # Grandparent
    grandparents = set()
    if ewe.parent_ewe:
        grandparents.add(ewe.parent_ewe.parent_ewe)
        grandparents.add(ewe.parent_ewe.parent_ram)
    if ewe.parent_ram:
        grandparents.add(ewe.parent_ram.parent_ewe)
        grandparents.add(ewe.parent_ram.parent_ram)
    grandparents = {gp for gp in grandparents if gp}
    if ram in grandparents:
        relationships.append("Grandparent-Grandchild")
    
    # Niece/nephew
    ram_nieces_nephews = get_nieces_and_nephews(ram)
    if ewe in ram_nieces_nephews:
        relationships.append("Niece")
    
    ewe_nieces_nephews = get_nieces_and_nephews(ewe)
    if ram in ewe_nieces_nephews:
        relationships.append("Nephew")
    
    # First cousins
    if are_first_cousins(ewe, ram):
        relationships.append("First Cousins")
    
    return relationships if relationships else ["No close relationship detected"]

def check_ram_capacity(ram, start_date):
    """Check if ram has exceeded breeding capacity for the season"""
    breed_capacity = {
        'PD': 55,
        'PA': 40,
        'LOCAL': 40,
        'AC': 40,
        'DC': 40,
    }
    
    season_start = datetime(start_date.year, 1, 1).date()
    season_end = datetime(start_date.year, 12, 31).date()
    
    current_cycles = BreedingCycle.objects.filter(
        ram=ram,
        start_date__range=[season_start, season_end],
        status__in=['PLANNED', 'IN_PROGRESS']
    ).count()
    
    capacity = breed_capacity.get(ram.breed, 40)
    return current_cycles < capacity