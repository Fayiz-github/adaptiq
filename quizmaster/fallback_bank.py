"""
fallback_bank.py
----------------
Deterministic, high-quality curated fallback question bank for Class 8 curriculum.
Guarantees 100% zero-crash uptime in case of external LLM API rate limits, timeouts,
or temporary network disconnection.
"""

from core.models import Question

FALLBACK_QUESTIONS: dict[str, dict[str, list[dict]]] = {
    "Mathematics": {
        "Rational Numbers": [
            {
                "level": "easy",
                "question_text": "Which of the following numbers is a rational number?",
                "options": {
                    "A": "√2",
                    "B": "π",
                    "C": "-3/5",
                    "D": "√5"
                },
                "correct_answer": "C"
            },
            {
                "level": "easy",
                "question_text": "What is the additive inverse of -7/9?",
                "options": {
                    "A": "9/7",
                    "B": "7/9",
                    "C": "-9/7",
                    "D": "0"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "Find a rational number between 1/4 and 1/2.",
                "options": {
                    "A": "3/8",
                    "B": "5/8",
                    "C": "1/8",
                    "D": "7/8"
                },
                "correct_answer": "A"
            },
            {
                "level": "medium",
                "question_text": "What is the multiplicative inverse (reciprocal) of (-5/8) × (-3/7)?",
                "options": {
                    "A": "15/56",
                    "B": "-56/15",
                    "C": "56/15",
                    "D": "-15/56"
                },
                "correct_answer": "C"
            },
            {
                "level": "hard",
                "question_text": "If x = 2/3 and y = -3/4, what is the value of (x + y) ÷ (x - y)?",
                "options": {
                    "A": "-1/17",
                    "B": "1/17",
                    "C": "-7/17",
                    "D": "-1/7"
                },
                "correct_answer": "A"
            }
        ],
        "Linear Equations": [
            {
                "level": "easy",
                "question_text": "Solve for x: 3x - 5 = 10",
                "options": {
                    "A": "3",
                    "B": "5",
                    "C": "15",
                    "D": "4"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "In the equation 2y + 9 = 4, what is the degree of the equation?",
                "options": {
                    "A": "1",
                    "B": "2",
                    "C": "0",
                    "D": "9"
                },
                "correct_answer": "A"
            },
            {
                "level": "medium",
                "question_text": "Solve for x: 5x + 9 = 5 + 3x",
                "options": {
                    "A": "2",
                    "B": "-2",
                    "C": "7",
                    "D": "-7"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "The perimeter of a rectangle is 26 cm. If its width is 4 cm, what is its length?",
                "options": {
                    "A": "9 cm",
                    "B": "11 cm",
                    "C": "8 cm",
                    "D": "18 cm"
                },
                "correct_answer": "A"
            },
            {
                "level": "hard",
                "question_text": "The sum of three consecutive multiples of 8 is 888. Find the smallest multiple.",
                "options": {
                    "A": "280",
                    "B": "288",
                    "C": "296",
                    "D": "272"
                },
                "correct_answer": "B"
            }
        ],
        "Mensuration": [
            {
                "level": "easy",
                "question_text": "What is the formula for the area of a trapezium with parallel sides a and b, and height h?",
                "options": {
                    "A": "a × b × h",
                    "B": "1/2 × (a + b) × h",
                    "C": "2 × (a + b) × h",
                    "D": "1/2 × a × b × h"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "What is the total surface area of a cube having side length 'a'?",
                "options": {
                    "A": "4a²",
                    "B": "6a²",
                    "C": "a³",
                    "D": "12a"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "Find the volume of a cylinder whose base radius is 7 cm and height is 10 cm (Take π = 22/7).",
                "options": {
                    "A": "1540 cm³",
                    "B": "1440 cm³",
                    "C": "770 cm³",
                    "D": "440 cm³"
                },
                "correct_answer": "A"
            },
            {
                "level": "medium",
                "question_text": "The diagonal of a quadrilateral shaped field is 24 m and the perpendiculars dropped on it from the remaining opposite vertices are 8 m and 13 m. What is the area of the field?",
                "options": {
                    "A": "504 m²",
                    "B": "252 m²",
                    "C": "168 m²",
                    "D": "216 m²"
                },
                "correct_answer": "B"
            },
            {
                "level": "hard",
                "question_text": "A road roller takes 750 complete revolutions to move once over to level a road. If the diameter of the roller is 84 cm and length is 1 m, what is the road area?",
                "options": {
                    "A": "1980 m²",
                    "B": "2640 m²",
                    "C": "1800 m²",
                    "D": "1500 m²"
                },
                "correct_answer": "A"
            }
        ],
        "Exponents & Powers": [
            {
                "level": "easy",
                "question_text": "What is the value of 5⁻²?",
                "options": {
                    "A": "-10",
                    "B": "-25",
                    "C": "1/25",
                    "D": "1/10"
                },
                "correct_answer": "C"
            },
            {
                "level": "easy",
                "question_text": "Any non-zero rational number raised to the power 0 is equal to:",
                "options": {
                    "A": "0",
                    "B": "1",
                    "C": "Infinity",
                    "D": "The number itself"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "Simplify: (2⁵ ÷ 2⁸) × 2⁻⁵",
                "options": {
                    "A": "2⁻⁸",
                    "B": "2⁸",
                    "C": "2⁻²",
                    "D": "2⁰"
                },
                "correct_answer": "A"
            },
            {
                "level": "medium",
                "question_text": "Express 0.000035 in standard scientific notation.",
                "options": {
                    "A": "3.5 × 10⁻⁵",
                    "B": "3.5 × 10⁻⁴",
                    "C": "35 × 10⁻⁶",
                    "D": "0.35 × 10⁻⁴"
                },
                "correct_answer": "A"
            },
            {
                "level": "hard",
                "question_text": "Find the value of m for which 5ᵐ ÷ 5⁻³ = 5⁵.",
                "options": {
                    "A": "2",
                    "B": "8",
                    "C": "-2",
                    "D": "15"
                },
                "correct_answer": "A"
            }
        ],
        "Data Handling": [
            {
                "level": "easy",
                "question_text": "What is the central angle of a complete pie chart circle?",
                "options": {
                    "A": "90°",
                    "B": "180°",
                    "C": "360°",
                    "D": "270°"
                },
                "correct_answer": "C"
            },
            {
                "level": "easy",
                "question_text": "When a standard fair six-sided die is rolled, what is the probability of getting an even number?",
                "options": {
                    "A": "1/6",
                    "B": "1/3",
                    "C": "1/2",
                    "D": "2/3"
                },
                "correct_answer": "C"
            },
            {
                "level": "medium",
                "question_text": "In a histogram, the width of each bar represents which of the following?",
                "options": {
                    "A": "Class frequency",
                    "B": "Class width / interval",
                    "C": "Cumulative frequency",
                    "D": "Total sample size"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "A bag has 4 red balls and 6 yellow balls. If one ball is drawn at random, what is the probability of getting a red ball?",
                "options": {
                    "A": "2/5",
                    "B": "3/5",
                    "C": "4/6",
                    "D": "1/4"
                },
                "correct_answer": "A"
            },
            {
                "level": "hard",
                "question_text": "In a school of 720 students, 180 like Cricket. What is the central angle representing Cricket in a pie chart?",
                "options": {
                    "A": "45°",
                    "B": "90°",
                    "C": "60°",
                    "D": "120°"
                },
                "correct_answer": "B"
            }
        ]
    },
    "Biology": {
        "Cell Structure": [
            {
                "level": "easy",
                "question_text": "Which organelle is universally referred to as the 'Powerhouse of the Cell'?",
                "options": {
                    "A": "Ribosome",
                    "B": "Mitochondria",
                    "C": "Golgi apparatus",
                    "D": "Lysosome"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "Which cell structure is present in plant cells but absent in animal cells?",
                "options": {
                    "A": "Cell membrane",
                    "B": "Cytoplasm",
                    "C": "Cell wall",
                    "D": "Nucleus"
                },
                "correct_answer": "C"
            },
            {
                "level": "medium",
                "question_text": "What is the primary function of chloroplasts in plant cells?",
                "options": {
                    "A": "Protein synthesis",
                    "B": "Trapping solar energy for photosynthesis",
                    "C": "Cellular respiration",
                    "D": "Lipid secretion"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "Which part of the nucleus contains hereditary material called genes?",
                "options": {
                    "A": "Nuclear membrane",
                    "B": "Nucleolus",
                    "C": "Chromosomes",
                    "D": "Vacuole"
                },
                "correct_answer": "C"
            },
            {
                "level": "hard",
                "question_text": "Why do plant cells require a rigid cell wall, unlike animal cells?",
                "options": {
                    "A": "To synthesize ATP in low oxygen environments",
                    "B": "To withstand turgor pressure and environmental temperature/wind variations",
                    "C": "To prevent entry of water via osmosis",
                    "D": "To digest cellular metabolic waste"
                },
                "correct_answer": "B"
            }
        ],
        "Photosynthesis": [
            {
                "level": "easy",
                "question_text": "Which green pigment in leaves is essential for absorbing sunlight during photosynthesis?",
                "options": {
                    "A": "Carotene",
                    "B": "Chlorophyll",
                    "C": "Xanthophyll",
                    "D": "Anthocyanin"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "Which gas is released into the atmosphere as a byproduct of photosynthesis?",
                "options": {
                    "A": "Carbon dioxide",
                    "B": "Nitrogen",
                    "C": "Oxygen",
                    "D": "Hydrogen"
                },
                "correct_answer": "C"
            },
            {
                "level": "medium",
                "question_text": "Through which microscopic pores on leaf surfaces does carbon dioxide enter for photosynthesis?",
                "options": {
                    "A": "Stomata",
                    "B": "Lenticels",
                    "C": "Vascular bundles",
                    "D": "Xylem vessels"
                },
                "correct_answer": "A"
            },
            {
                "level": "medium",
                "question_text": "What are the primary chemical end-products of the photosynthesis reaction?",
                "options": {
                    "A": "Glucose and Oxygen",
                    "B": "Water and Carbon Dioxide",
                    "C": "Starch and Nitrogen",
                    "D": "Lactic acid and ATP"
                },
                "correct_answer": "A"
            },
            {
                "level": "hard",
                "question_text": "In a de-starched potted plant, if part of a green leaf is covered with black paper and exposed to sunlight for 4 hours, what will the iodine starch test show?",
                "options": {
                    "A": "The covered part turns blue-black, uncovered part stays brown",
                    "B": "The entire leaf turns blue-black",
                    "C": "The uncovered part turns blue-black, covered part stays brown",
                    "D": "Neither part changes color"
                },
                "correct_answer": "C"
            }
        ],
        "Microorganisms": [
            {
                "level": "easy",
                "question_text": "Which bacterium is responsible for the coagulation of milk into curd?",
                "options": {
                    "A": "Rhizobium",
                    "B": "Lactobacillus",
                    "C": "Streptococcus",
                    "D": "Escherichia coli"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "Penicillin, the first widely used antibiotic, was discovered by:",
                "options": {
                    "A": "Louis Pasteur",
                    "B": "Alexander Fleming",
                    "C": "Edward Jenner",
                    "D": "Robert Koch"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "Which microorganism plays an indispensable role in biological nitrogen fixation in leguminous plant root nodules?",
                "options": {
                    "A": "Yeast",
                    "B": "Amoeba",
                    "C": "Rhizobium",
                    "D": "Penicillium"
                },
                "correct_answer": "C"
            },
            {
                "level": "medium",
                "question_text": "Which of the following diseases is caused by a protozoan transmitted through the bite of a female Anopheles mosquito?",
                "options": {
                    "A": "Cholera",
                    "B": "Malaria",
                    "C": "Tuberculosis",
                    "D": "Typhoid"
                },
                "correct_answer": "B"
            },
            {
                "level": "hard",
                "question_text": "Why do viruses differ fundamentally from bacteria, fungi, and protozoa regarding biological classification and antibiotic treatment?",
                "options": {
                    "A": "Viruses have thicker chitin cell walls that repel penicillin",
                    "B": "Viruses reproduce only inside host cells and lack their own metabolic cell machinery",
                    "C": "Viruses are multicellular eukaryotes with flagella",
                    "D": "Viruses only infect marine invertebrates"
                },
                "correct_answer": "B"
            }
        ],
        "Reproduction": [
            {
                "level": "easy",
                "question_text": "What type of asexual reproduction is observed in Hydra where an outgrowth develops into a new individual?",
                "options": {
                    "A": "Binary fission",
                    "B": "Budding",
                    "C": "Spore formation",
                    "D": "Fragmentation"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "The fusion of a male gamete (sperm) with a female gamete (ovum) produces a single cell known as:",
                "options": {
                    "A": "Embryo",
                    "B": "Foetus",
                    "C": "Zygote",
                    "D": "Blastocyst"
                },
                "correct_answer": "C"
            },
            {
                "level": "medium",
                "question_text": "Animals that lay eggs with little or no embryonic development within the mother are termed:",
                "options": {
                    "A": "Viviparous",
                    "B": "Oviparous",
                    "C": "Hermaphrodites",
                    "D": "Parthenogenic"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "In human females, where does the fertilization of the ovum by sperm typically take place?",
                "options": {
                    "A": "Ovary",
                    "B": "Uterus",
                    "C": "Fallopian tube (Oviduct)",
                    "D": "Cervix"
                },
                "correct_answer": "C"
            },
            {
                "level": "hard",
                "question_text": "What is metamorphosis in amphibians such as frogs, and which hormone controls it?",
                "options": {
                    "A": "Transformation of larva to adult controlled by Thyroxine",
                    "B": "Direct development without larval stage controlled by Insulin",
                    "C": "Asexual division controlled by Adrenaline",
                    "D": "Cellular apoptosis controlled by Estrogen"
                },
                "correct_answer": "A"
            }
        ],
        "Life Processes": [
            {
                "level": "easy",
                "question_text": "Which blood vessels carry oxygenated blood away from the heart to body tissues?",
                "options": {
                    "A": "Veins",
                    "B": "Capillaries",
                    "C": "Arteries",
                    "D": "Vena cava"
                },
                "correct_answer": "C"
            },
            {
                "level": "easy",
                "question_text": "Which organ in the human body is primarily responsible for filtering nitrogenous waste (urea) from blood?",
                "options": {
                    "A": "Lungs",
                    "B": "Kidneys",
                    "C": "Liver",
                    "D": "Pancreas"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "What is the role of bile juice secreted by the liver in human digestion?",
                "options": {
                    "A": "Digesting carbohydrates into glucose",
                    "B": "Emulsification of large fat globules and providing an alkaline medium",
                    "C": "Breaking down proteins into amino acids",
                    "D": "Absorbing water in the large intestine"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "In plants, which specialized vascular tissue transports dissolved sugars synthesized in leaves to other growing parts?",
                "options": {
                    "A": "Xylem",
                    "B": "Phloem",
                    "C": "Pith",
                    "D": "Cortex"
                },
                "correct_answer": "B"
            },
            {
                "level": "hard",
                "question_text": "During vigorous muscular exercise in humans, why does muscle fatigue occur with cramp sensations?",
                "options": {
                    "A": "Excessive accumulation of carbon dioxide in alveoli",
                    "B": "Anaerobic respiration leading to lactic acid accumulation",
                    "C": "Excess synthesis of glycogen in mitochondria",
                    "D": "Depletion of extracellular calcium ions"
                },
                "correct_answer": "B"
            }
        ]
    },
    "Chemistry": {
        "States of Matter": [
            {
                "level": "easy",
                "question_text": "The transition of a solid directly into vapor phase without passing through liquid state is called:",
                "options": {
                    "A": "Condensation",
                    "B": "Sublimation",
                    "C": "Evaporation",
                    "D": "Deposition"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "Which state of matter has neither a definite shape nor a definite volume?",
                "options": {
                    "A": "Solid",
                    "B": "Liquid",
                    "C": "Gas",
                    "D": "Crystal"
                },
                "correct_answer": "C"
            },
            {
                "level": "medium",
                "question_text": "Why does a drop of ink spread faster in hot water than in cold water?",
                "options": {
                    "A": "Density of ink decreases at high pressure",
                    "B": "Higher temperature increases the kinetic energy and diffusion rate of particles",
                    "C": "Hot water molecules are stationary",
                    "D": "Ink dissolves due to chemical neutralization"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "During the melting of ice at 0°C, the temperature remains constant until all ice melts. What is this absorbed heat called?",
                "options": {
                    "A": "Specific heat capacity",
                    "B": "Latent heat of fusion",
                    "C": "Thermal expansion heat",
                    "D": "Latent heat of vaporization"
                },
                "correct_answer": "B"
            },
            {
                "level": "hard",
                "question_text": "Which conditions of temperature and pressure favor the liquefaction of gases?",
                "options": {
                    "A": "High temperature and low pressure",
                    "B": "Low temperature and high pressure",
                    "C": "Low temperature and low pressure",
                    "D": "High temperature and high pressure"
                },
                "correct_answer": "B"
            }
        ],
        "Atoms & Molecules": [
            {
                "level": "easy",
                "question_text": "Who proposed the Atomic Theory stating that all matter is composed of indivisible atoms?",
                "options": {
                    "A": "J.J. Thomson",
                    "B": "John Dalton",
                    "C": "Ernest Rutherford",
                    "D": "Niels Bohr"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "What is the chemical formula of common salt (sodium chloride)?",
                "options": {
                    "A": "NaCl",
                    "B": "Na₂CO₃",
                    "C": "NaHCO₃",
                    "D": "KCl"
                },
                "correct_answer": "A"
            },
            {
                "level": "medium",
                "question_text": "What is the atomicity of an Ozone molecule (O₃)?",
                "options": {
                    "A": "1 (Monoatomic)",
                    "B": "2 (Diatomic)",
                    "C": "3 (Triatomic)",
                    "D": "4 (Tetratomic)"
                },
                "correct_answer": "C"
            },
            {
                "level": "medium",
                "question_text": "According to the Law of Conservation of Mass in a chemical reaction:",
                "options": {
                    "A": "Mass of reactants is always greater than mass of products",
                    "B": "Total mass of products equals total mass of reactants",
                    "C": "Mass can be created if energy is absorbed",
                    "D": "Gas products have zero mass"
                },
                "correct_answer": "B"
            },
            {
                "level": "hard",
                "question_text": "What is the molecular mass of Calcium Carbonate (CaCO₃)? [Atomic masses: Ca=40, C=12, O=16]",
                "options": {
                    "A": "68 u",
                    "B": "100 u",
                    "C": "84 u",
                    "D": "112 u"
                },
                "correct_answer": "B"
            }
        ],
        "Acids & Bases": [
            {
                "level": "easy",
                "question_text": "What color does blue litmus paper turn when dipped into an acidic solution like lemon juice?",
                "options": {
                    "A": "Yellow",
                    "B": "Red",
                    "C": "Green",
                    "D": "Remains blue"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "Which organic acid is naturally present in curd and sour milk?",
                "options": {
                    "A": "Acetic acid",
                    "B": "Citric acid",
                    "C": "Lactic acid",
                    "D": "Tartaric acid"
                },
                "correct_answer": "C"
            },
            {
                "level": "medium",
                "question_text": "What are the typical products formed when an acid reacts with a base in a neutralization reaction?",
                "options": {
                    "A": "Salt and Hydrogen gas",
                    "B": "Salt and Water",
                    "C": "Metal oxide and Oxygen",
                    "D": "Base and Carbon dioxide"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "Why is calamine lotion (containing zinc carbonate) applied on the skin when an ant bites?",
                "options": {
                    "A": "To accelerate oxidation",
                    "B": "To neutralize the acidic formic acid injected by the ant",
                    "C": "To bleach the skin pigments",
                    "D": "To increase blood flow"
                },
                "correct_answer": "B"
            },
            {
                "level": "hard",
                "question_text": "Which gas is evolved when dilute hydrochloric acid reacts with sodium hydrogen carbonate?",
                "options": {
                    "A": "Hydrogen gas which burns with a pop sound",
                    "B": "Carbon dioxide gas which turns lime water milky",
                    "C": "Sulfur dioxide gas with pungent smell",
                    "D": "Chlorine gas which bleaches litmus"
                },
                "correct_answer": "B"
            }
        ],
        "Metals & Non-metals": [
            {
                "level": "easy",
                "question_text": "Which metal exists in liquid state at room temperature?",
                "options": {
                    "A": "Mercury",
                    "B": "Bromine",
                    "C": "Gallium",
                    "D": "Sodium"
                },
                "correct_answer": "A"
            },
            {
                "level": "easy",
                "question_text": "The property of metals that allows them to be beaten into thin sheets is termed:",
                "options": {
                    "A": "Ductility",
                    "B": "Malleability",
                    "C": "Sonority",
                    "D": "Conductivity"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "Why are sodium and potassium metals stored under kerosene oil?",
                "options": {
                    "A": "They evaporate rapidly at room temperature",
                    "B": "They react vigorously with moisture and oxygen in air producing heat and fire",
                    "C": "To prevent them from melting",
                    "D": "Kerosene dissolves metallic impurities"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "When an iron nail is immersed in a copper sulfate solution (CuSO₄), what change is observed after 30 minutes?",
                "options": {
                    "A": "Solution turns colorless and no deposit forms",
                    "B": "Blue solution turns light green and reddish-brown copper deposits on nail",
                    "C": "Solution turns bright yellow and iron dissolves completely",
                    "D": "Nail catches fire"
                },
                "correct_answer": "B"
            },
            {
                "level": "hard",
                "question_text": "Which non-metal is an allotrope of carbon that conducts electricity due to delocalized electrons?",
                "options": {
                    "A": "Diamond",
                    "B": "Graphite",
                    "C": "Fullerene",
                    "D": "Charcoal"
                },
                "correct_answer": "B"
            }
        ],
        "Chemical Reactions": [
            {
                "level": "easy",
                "question_text": "Burning of magnesium ribbon in air is an example of which type of chemical reaction?",
                "options": {
                    "A": "Decomposition reaction",
                    "B": "Combination reaction (Oxidation)",
                    "C": "Displacement reaction",
                    "D": "Neutralization reaction"
                },
                "correct_answer": "B"
            },
            {
                "level": "easy",
                "question_text": "What type of reaction releases heat energy into the surrounding environment?",
                "options": {
                    "A": "Endothermic reaction",
                    "B": "Exothermic reaction",
                    "C": "Electrochemical reaction",
                    "D": "Photochemical reaction"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "When zinc granules react with dilute sulfuric acid, which gas is liberated?",
                "options": {
                    "A": "Oxygen",
                    "B": "Hydrogen",
                    "C": "Sulfur dioxide",
                    "D": "Nitrogen"
                },
                "correct_answer": "B"
            },
            {
                "level": "medium",
                "question_text": "In the reaction: CuO + H₂ → Cu + H₂O, which substance undergoes oxidation?",
                "options": {
                    "A": "CuO",
                    "B": "H₂",
                    "C": "Cu",
                    "D": "H₂O"
                },
                "correct_answer": "B"
            },
            {
                "level": "hard",
                "question_text": "Why does iron rust faster in coastal saline water than in inland freshwater?",
                "options": {
                    "A": "Saline water lacks dissolved oxygen",
                    "B": "Salt ions (electrolytes) increase the electrical conductivity of water, accelerating electrochemical oxidation",
                    "C": "Salt acts as a physical barrier preventing rust removal",
                    "D": "Freshwater reacts chemically with iron to form a protective oxide coat"
                },
                "correct_answer": "B"
            }
        ]
    }
}


def get_fallback_question(subject: str, topic: str, level: str, exclude_texts: list[str] | None = None) -> Question:
    """
    Retrieves a curated question from the fallback bank for the specified topic and level.
    Avoids returning questions matching exclude_texts when candidates exist.
    """
    import uuid
    exclude_texts = [t.strip().lower() for t in (exclude_texts or [])]

    subject_data = FALLBACK_QUESTIONS.get(subject, {})
    topic_data = subject_data.get(topic, [])
    
    # Filter by level
    candidates = [q for q in topic_data if q["level"].lower() == level.lower()]
    
    # Filter out already asked
    fresh = [q for q in candidates if q["question_text"].strip().lower() not in exclude_texts]
    selected_data = fresh[0] if fresh else (candidates[0] if candidates else None)

    if not selected_data and topic_data:
        selected_data = topic_data[0]

    if not selected_data:
        # Ultimate fallback
        selected_data = {
            "level": level,
            "question_text": f"What is a foundational principle of {topic} in Class 8 {subject}?",
            "options": {
                "A": f"Core concept governing {topic}",
                "B": f"Secondary trait of {topic}",
                "C": "Unrelated historical conjecture",
                "D": "None of the above"
            },
            "correct_answer": "A"
        }

    return Question(
        question_id=str(uuid.uuid4()),
        subject=subject,
        topic=topic,
        level=selected_data["level"],
        question_text=selected_data["question_text"],
        options=selected_data["options"],
        correct_answer=selected_data["correct_answer"]
    )
