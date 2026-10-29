"""
Seed the QuizNest database with JEE Main/Advanced preparation content:
subjects, topics, a verified sample question bank, and a handful of
ready-to-take quizzes (topic-wise + full mock tests) so the site can be
tested immediately.

Usage:
    python seed_jee_data.py

Safe to re-run: subjects/topics use INSERT OR IGNORE, and quizzes are only
created the first time (the script checks whether they already exist).
"""

from app import init_db, get_db, execute_db, query_db, now_iso

# ---------------------------------------------------------------------------
# 1. Subjects & topics (full JEE syllabus categories requested)
# ---------------------------------------------------------------------------
SYLLABUS = {
    "Physics": [
        "Mechanics", "Thermodynamics", "Electrostatics", "Current Electricity",
        "Magnetism", "Electromagnetic Induction", "Optics", "Modern Physics",
        "SHM & Waves",
    ],
    "Chemistry": [
        "Physical Chemistry", "Organic Chemistry", "Inorganic Chemistry",
        "Atomic Structure", "Chemical Bonding", "Thermodynamics",
        "Equilibrium", "Electrochemistry", "Coordination Compounds",
    ],
    "Mathematics": [
        "Algebra", "Calculus", "Coordinate Geometry", "Trigonometry",
        "Vectors & 3D Geometry", "Probability & Statistics", "Complex Numbers",
        "Matrices & Determinants", "Sequence & Series",
    ],
}

# ---------------------------------------------------------------------------
# 2. Sample question bank — every answer has been checked for correctness.
#    Fields: topic, question, options A-D, correct letter, explanation,
#    difficulty, marks.
# ---------------------------------------------------------------------------
QUESTIONS = {
    "Physics": [
        dict(topic="Mechanics",
             q="A body of mass 2 kg is acted upon by a net force of 10 N. What is its acceleration?",
             a="2 m/s²", b="5 m/s²", c="10 m/s²", d="20 m/s²", correct="B",
             exp="By Newton's second law, a = F/m = 10/2 = 5 m/s².",
             difficulty="Easy", marks=4),
        dict(topic="Mechanics",
             q="A block slides down a frictionless incline from height h. What is its speed at the bottom?",
             a="√(gh)", b="√(2gh)", c="2gh", d="gh/2", correct="B",
             exp="By conservation of energy, mgh = ½mv², giving v = √(2gh).",
             difficulty="Medium", marks=4),
        dict(topic="Mechanics",
             q="The escape velocity of a body from Earth's surface is approximately:",
             a="7.9 km/s", b="11.2 km/s", c="25 km/s", d="42.1 km/s", correct="B",
             exp="Using ve = √(2GM/R) with Earth's mass and radius gives ve ≈ 11.2 km/s.",
             difficulty="Hard", marks=4),
        dict(topic="Thermodynamics",
             q="According to the first law of thermodynamics, the heat supplied to a system equals:",
             a="the change in internal energy plus the work done by the system",
             b="only the work done by the system",
             c="only the change in internal energy",
             d="the change in kinetic energy alone", correct="A",
             exp="First law: ΔQ = ΔU + ΔW (heat = change in internal energy + work done by the system).",
             difficulty="Easy", marks=4),
        dict(topic="Thermodynamics",
             q="A Carnot engine operates between 600 K and 300 K. What is its efficiency?",
             a="25%", b="50%", c="75%", d="100%", correct="B",
             exp="η = 1 − T2/T1 = 1 − 300/600 = 0.5 = 50%.",
             difficulty="Medium", marks=4),
        dict(topic="Electrostatics",
             q="If the distance between two point charges is doubled, the electrostatic force between them becomes:",
             a="half", b="one-fourth", c="double", d="four times", correct="B",
             exp="Coulomb's law: F ∝ 1/r². Doubling r reduces F to (1/2)² = 1/4 of its original value.",
             difficulty="Easy", marks=4),
        dict(topic="Electrostatics",
             q="The electric field inside a conductor in electrostatic equilibrium is:",
             a="maximum", b="zero", c="equal to the surface field", d="infinite", correct="B",
             exp="Free charges rearrange until the net field inside a conductor is zero in electrostatic equilibrium.",
             difficulty="Medium", marks=4),
        dict(topic="Current Electricity",
             q="A resistor carries a potential difference of 10 V and has resistance 2 Ω. What current flows through it?",
             a="2 A", b="5 A", c="10 A", d="20 A", correct="B",
             exp="By Ohm's law, I = V/R = 10/2 = 5 A.",
             difficulty="Easy", marks=4),
        dict(topic="Current Electricity",
             q="Two resistors of 4 Ω each are connected in parallel. What is the equivalent resistance?",
             a="1 Ω", b="2 Ω", c="4 Ω", d="8 Ω", correct="B",
             exp="For parallel resistors: 1/Rp = 1/4 + 1/4 = 1/2, so Rp = 2 Ω.",
             difficulty="Medium", marks=4),
        dict(topic="Magnetism",
             q="The SI unit of magnetic field (magnetic flux density) is:",
             a="Weber", b="Tesla", c="Henry", d="Gauss", correct="B",
             exp="Magnetic flux density is measured in Tesla (Wb/m²) in the SI system.",
             difficulty="Easy", marks=4),
        dict(topic="Magnetism",
             q="A current-carrying conductor in a magnetic field experiences maximum force when the angle between the current and the field is:",
             a="0°", b="45°", c="90°", d="180°", correct="C",
             exp="F = BIL sinθ is maximum when sinθ = 1, i.e., θ = 90°.",
             difficulty="Medium", marks=4),
        dict(topic="Electromagnetic Induction",
             q="Lenz's law is a consequence of the conservation of:",
             a="charge", b="energy", c="momentum", d="mass", correct="B",
             exp="The induced EMF opposes the change in flux, which follows directly from energy conservation.",
             difficulty="Medium", marks=4),
        dict(topic="Optics",
             q="If the refractive index of a medium is 1.5, the speed of light in that medium is approximately:",
             a="1.5 × 10⁸ m/s", b="2.0 × 10⁸ m/s", c="3.0 × 10⁸ m/s", d="4.5 × 10⁸ m/s", correct="B",
             exp="n = c/v, so v = c/n = (3 × 10⁸)/1.5 = 2 × 10⁸ m/s.",
             difficulty="Medium", marks=4),
        dict(topic="Modern Physics",
             q="In the photoelectric effect, the maximum kinetic energy of emitted electrons is given by:",
             a="KE = hν + φ", b="KE = hν − φ", c="KE = φ − hν", d="KE = hφ", correct="B",
             exp="Einstein's photoelectric equation: KEmax = hν − φ, where φ is the work function.",
             difficulty="Hard", marks=4),
        dict(topic="SHM & Waves",
             q="The time period of a simple pendulum of length l at a place with gravitational acceleration g is:",
             a="T = 2π√(l/g)", b="T = 2π√(g/l)", c="T = 2π(l/g)", d="T = π√(l/g)", correct="A",
             exp="For small oscillations, the time period of a simple pendulum is T = 2π√(l/g).",
             difficulty="Easy", marks=4),
    ],
    "Chemistry": [
        dict(topic="Physical Chemistry",
             q="What is the molarity of a solution containing 2 moles of solute in 4 litres of solution?",
             a="0.5 M", b="1 M", c="2 M", d="4 M", correct="A",
             exp="Molarity = moles of solute / volume of solution in litres = 2/4 = 0.5 M.",
             difficulty="Easy", marks=4),
        dict(topic="Physical Chemistry",
             q="For a first-order reaction, the unit of the rate constant k is:",
             a="s⁻¹", b="mol L⁻¹ s⁻¹", c="L mol⁻¹ s⁻¹", d="mol² L⁻² s⁻¹", correct="A",
             exp="For a first-order reaction, rate = k[A], so k has units of (time)⁻¹, i.e., s⁻¹.",
             difficulty="Medium", marks=4),
        dict(topic="Organic Chemistry",
             q="What is the IUPAC name of CH₄?",
             a="Methane", b="Ethane", c="Methanol", d="Methanal", correct="A",
             exp="CH₄ is the simplest alkane, named methane.",
             difficulty="Easy", marks=4),
        dict(topic="Organic Chemistry",
             q="Which functional group is present in an alcohol?",
             a="-COOH", b="-CHO", c="-OH", d="-NH₂", correct="C",
             exp="Alcohols are characterised by the hydroxyl (-OH) functional group.",
             difficulty="Easy", marks=4),
        dict(topic="Organic Chemistry",
             q="According to Markovnikov's rule, when HBr adds to an unsymmetrical alkene, the H atom attaches to the carbon that:",
             a="already has fewer hydrogen atoms",
             b="already has more hydrogen atoms",
             c="is part of a ring",
             d="is farthest from the double bond", correct="B",
             exp="Markovnikov's rule: the H adds to the carbon of the double bond that already carries more hydrogens.",
             difficulty="Hard", marks=4),
        dict(topic="Inorganic Chemistry",
             q="Which element is the most abundant by mass in the Earth's crust?",
             a="Silicon", b="Aluminium", c="Oxygen", d="Iron", correct="C",
             exp="Oxygen makes up roughly 46% of the Earth's crust by mass, more than any other element.",
             difficulty="Easy", marks=4),
        dict(topic="Inorganic Chemistry",
             q="Elements of Group 17 of the periodic table are commonly known as:",
             a="Alkali metals", b="Alkaline earth metals", c="Halogens", d="Noble gases", correct="C",
             exp="Group 17 elements (F, Cl, Br, I, At) are called halogens.",
             difficulty="Easy", marks=4),
        dict(topic="Atomic Structure",
             q="The energy of an electron in the n = 2 orbit of a hydrogen atom is:",
             a="-13.6 eV", b="-6.8 eV", c="-3.4 eV", d="-1.51 eV", correct="C",
             exp="En = -13.6/n² eV. For n = 2, En = -13.6/4 = -3.4 eV.",
             difficulty="Medium", marks=4),
        dict(topic="Chemical Bonding",
             q="What is the shape of the methane (CH₄) molecule according to VSEPR theory?",
             a="Linear", b="Trigonal planar", c="Tetrahedral", d="Octahedral", correct="C",
             exp="Carbon in CH₄ is sp³ hybridised with four bond pairs and no lone pairs, giving a tetrahedral shape.",
             difficulty="Medium", marks=4),
        dict(topic="Chemical Bonding",
             q="Sodium chloride (NaCl) is held together primarily by which type of bond?",
             a="Covalent bond", b="Ionic bond", c="Metallic bond", d="Hydrogen bond", correct="B",
             exp="Na transfers an electron to Cl, forming Na⁺ and Cl⁻ ions held by electrostatic (ionic) attraction.",
             difficulty="Easy", marks=4),
        dict(topic="Thermodynamics",
             q="A reaction is spontaneous at constant temperature and pressure when:",
             a="ΔG > 0", b="ΔG = 0", c="ΔG < 0", d="ΔH = 0", correct="C",
             exp="ΔG = ΔH − TΔS; a process is spontaneous when the Gibbs free energy change is negative.",
             difficulty="Medium", marks=4),
        dict(topic="Equilibrium",
             q="According to Le Chatelier's principle, if the pressure on a gaseous equilibrium is increased, the equilibrium shifts towards:",
             a="the side with more moles of gas",
             b="the side with fewer moles of gas",
             c="whichever side is exothermic",
             d="no shift occurs", correct="B",
             exp="Increasing pressure shifts equilibrium towards the side with fewer gas moles, reducing pressure.",
             difficulty="Medium", marks=4),
        dict(topic="Electrochemistry",
             q="The standard electrode potential of the standard hydrogen electrode (SHE) is defined as:",
             a="+1 V", b="0 V", c="-1 V", d="2.4 V", correct="B",
             exp="The SHE is the reference electrode and is assigned a standard potential of exactly 0 V.",
             difficulty="Easy", marks=4),
        dict(topic="Electrochemistry",
             q="In the Nernst equation, as the concentration of reactant ions increases (for a reduction half-reaction), the electrode potential:",
             a="increases", b="decreases", c="remains unchanged", d="becomes zero", correct="A",
             exp="E = E° − (RT/nF)lnQ; increasing reactant (ion) concentration decreases Q, increasing E.",
             difficulty="Hard", marks=4),
        dict(topic="Coordination Compounds",
             q="What is the coordination number of cobalt in the complex [Co(NH₃)₆]³⁺?",
             a="3", b="4", c="6", d="8", correct="C",
             exp="Six NH₃ ligands are directly bonded to the central Co³⁺ ion, giving a coordination number of 6.",
             difficulty="Easy", marks=4),
    ],
    "Mathematics": [
        dict(topic="Algebra",
             q="What are the roots of the quadratic equation x² − 5x + 6 = 0?",
             a="1, 6", b="2, 3", c="-2, -3", d="1, 5", correct="B",
             exp="Factoring: (x−2)(x−3) = 0, so x = 2 or x = 3.",
             difficulty="Easy", marks=4),
        dict(topic="Algebra",
             q="For the quadratic equation ax² + bx + c = 0, the sum of the roots is:",
             a="-b/a", b="b/a", c="c/a", d="-c/a", correct="A",
             exp="Sum of roots = -b/a and product of roots = c/a, from Vieta's formulas.",
             difficulty="Medium", marks=4),
        dict(topic="Calculus",
             q="What is the derivative of x³ with respect to x?",
             a="x²", b="3x", c="3x²", d="x³/3", correct="C",
             exp="Using the power rule, d/dx(xⁿ) = nx^(n−1), so d/dx(x³) = 3x².",
             difficulty="Easy", marks=4),
        dict(topic="Calculus",
             q="What is ∫(1/x) dx?",
             a="x²/2 + C", b="ln|x| + C", c="1/x² + C", d="-1/x² + C", correct="B",
             exp="The standard integral ∫(1/x)dx = ln|x| + C.",
             difficulty="Medium", marks=4),
        dict(topic="Calculus",
             q="What is the value of lim(x→0) (sin x)/x?",
             a="0", b="1", c="∞", d="undefined", correct="B",
             exp="This is a standard limit: lim(x→0) sinx/x = 1.",
             difficulty="Hard", marks=4),
        dict(topic="Coordinate Geometry",
             q="What is the distance between the points (0, 0) and (3, 4)?",
             a="3", b="4", c="5", d="7", correct="C",
             exp="Distance = √((3−0)² + (4−0)²) = √(9+16) = √25 = 5.",
             difficulty="Easy", marks=4),
        dict(topic="Coordinate Geometry",
             q="What is the slope of the line passing through the points (1, 2) and (3, 6)?",
             a="1", b="2", c="3", d="4", correct="B",
             exp="Slope = (6−2)/(3−1) = 4/2 = 2.",
             difficulty="Medium", marks=4),
        dict(topic="Trigonometry",
             q="What is the value of sin²θ + cos²θ?",
             a="0", b="1", c="2", d="depends on θ", correct="B",
             exp="This is the fundamental Pythagorean trigonometric identity: sin²θ + cos²θ = 1 for all θ.",
             difficulty="Easy", marks=4),
        dict(topic="Trigonometry",
             q="What is the value of sin 30°?",
             a="0", b="1/2", c="√3/2", d="1", correct="B",
             exp="sin 30° = 1/2 is a standard trigonometric value.",
             difficulty="Easy", marks=4),
        dict(topic="Vectors & 3D Geometry",
             q="What is the magnitude of the vector (3, 4, 0)?",
             a="3", b="4", c="5", d="7", correct="C",
             exp="|v| = √(3² + 4² + 0²) = √25 = 5.",
             difficulty="Easy", marks=4),
        dict(topic="Vectors & 3D Geometry",
             q="If the dot product of two non-zero vectors is zero, the vectors are:",
             a="parallel", b="perpendicular", c="equal", d="opposite", correct="B",
             exp="a·b = |a||b|cosθ = 0 implies cosθ = 0, so θ = 90°, i.e., the vectors are perpendicular.",
             difficulty="Medium", marks=4),
        dict(topic="Probability & Statistics",
             q="What is the probability of getting a head when a fair coin is tossed once?",
             a="1/4", b="1/3", c="1/2", d="1", correct="C",
             exp="A fair coin has two equally likely outcomes, so P(head) = 1/2.",
             difficulty="Easy", marks=4),
        dict(topic="Probability & Statistics",
             q="What is the probability of getting a sum of 7 when two fair dice are rolled?",
             a="1/12", b="1/6", c="1/4", d="5/36", correct="B",
             exp="There are 6 favourable outcomes (out of 36) that sum to 7, so P = 6/36 = 1/6.",
             difficulty="Medium", marks=4),
        dict(topic="Complex Numbers",
             q="What is the value of i⁴, where i = √−1?",
             a="-1", b="1", c="i", d="-i", correct="B",
             exp="i² = −1, so i⁴ = (i²)² = (−1)² = 1.",
             difficulty="Easy", marks=4),
        dict(topic="Complex Numbers",
             q="What is the modulus of the complex number 3 + 4i?",
             a="3", b="4", c="5", d="7", correct="C",
             exp="|z| = √(3² + 4²) = √25 = 5.",
             difficulty="Medium", marks=4),
        dict(topic="Matrices & Determinants",
             q="What is the determinant of the matrix [[2, 3], [1, 4]]?",
             a="5", b="8", c="11", d="-5", correct="A",
             exp="For a 2×2 matrix [[a,b],[c,d]], det = ad − bc = (2)(4) − (3)(1) = 8 − 3 = 5.",
             difficulty="Easy", marks=4),
        dict(topic="Sequence & Series",
             q="What is the sum of the first 10 natural numbers?",
             a="45", b="50", c="55", d="100", correct="C",
             exp="Sum = n(n+1)/2 = 10×11/2 = 55.",
             difficulty="Easy", marks=4),
        dict(topic="Sequence & Series",
             q="In an arithmetic progression with first term a and common difference d, the nth term is:",
             a="a + nd", b="a + (n−1)d", c="a × d^(n−1)", d="a − (n−1)d", correct="B",
             exp="The nth term of an AP is given by Tn = a + (n−1)d.",
             difficulty="Medium", marks=4),
    ],
}

# Topics chosen to also get a dedicated topic-wise quiz (need >= 2 questions each)
FEATURED_TOPIC_QUIZ = {
    "Physics": "Mechanics",
    "Chemistry": "Organic Chemistry",
    "Mathematics": "Calculus",
}


def seed():
    init_db()

    # ---- subjects & topics -------------------------------------------------
    subject_ids = {}
    topic_ids = {}
    for subject_name, topics in SYLLABUS.items():
        row = query_db("SELECT id FROM subjects WHERE name = ?", (subject_name,), one=True)
        if row:
            subject_id = row["id"]
        else:
            subject_id = execute_db("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
            print(f"Created subject: {subject_name}")
        subject_ids[subject_name] = subject_id

        for topic_name in topics:
            trow = query_db(
                "SELECT id FROM topics WHERE subject_id = ? AND name = ?",
                (subject_id, topic_name), one=True,
            )
            if trow:
                topic_id = trow["id"]
            else:
                topic_id = execute_db(
                    "INSERT INTO topics (subject_id, name) VALUES (?, ?)", (subject_id, topic_name)
                )
            topic_ids[(subject_name, topic_name)] = topic_id

    # ---- questions ----------------------------------------------------------
    existing_question_count = query_db("SELECT COUNT(*) c FROM questions", one=True)["c"]
    inserted_ids = {}  # subject -> topic -> [question_id,...]
    if existing_question_count > 0:
        print(f"Questions table already has {existing_question_count} rows — skipping question seeding.")
    else:
        for subject_name, questions in QUESTIONS.items():
            subject_id = subject_ids[subject_name]
            for item in questions:
                topic_id = topic_ids[(subject_name, item["topic"])]
                qid = execute_db(
                    """
                    INSERT INTO questions
                        (subject_id, topic_id, question_text, option_a, option_b, option_c, option_d,
                         correct_option, explanation, difficulty, marks, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (subject_id, topic_id, item["q"], item["a"], item["b"], item["c"], item["d"],
                     item["correct"], item["exp"], item["difficulty"], item["marks"], now_iso()),
                )
                inserted_ids.setdefault(subject_name, {}).setdefault(item["topic"], []).append(qid)
        total = sum(len(v) for subj in inserted_ids.values() for v in subj.values())
        print(f"Inserted {total} sample JEE questions.")

    # ---- quizzes --------------------------------------------------------------
    existing_quiz_count = query_db("SELECT COUNT(*) c FROM quizzes", one=True)["c"]
    if existing_quiz_count > 0:
        print(f"Quizzes table already has {existing_quiz_count} rows — skipping quiz seeding.")
        return

    def make_quiz(title, description, subject_id, topic_id, is_mock, duration, question_ids):
        quiz_id = execute_db(
            """
            INSERT INTO quizzes (title, description, subject_id, topic_id, is_mock, duration_minutes,
                                  created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (title, description, subject_id, topic_id, is_mock, duration, now_iso()),
        )
        for pos, qid in enumerate(question_ids, start=1):
            execute_db(
                "INSERT INTO quiz_questions (quiz_id, question_id, position) VALUES (?, ?, ?)",
                (quiz_id, qid, pos),
            )
        return quiz_id

    all_by_subject = {}
    for subject_name in SYLLABUS:
        all_ids = query_db(
            "SELECT id FROM questions WHERE subject_id = ? ORDER BY id", (subject_ids[subject_name],)
        )
        all_by_subject[subject_name] = [r["id"] for r in all_ids]

        # Full-subject practice set
        make_quiz(
            f"{subject_name} — Full Practice Set",
            f"All available {subject_name} questions spanning multiple topics. Good all-round practice.",
            subject_ids[subject_name], None, 0,
            max(10, len(all_by_subject[subject_name]) * 2),
            all_by_subject[subject_name],
        )

        # Featured topic-wise quiz
        featured_topic = FEATURED_TOPIC_QUIZ.get(subject_name)
        if featured_topic:
            topic_q_ids = query_db(
                "SELECT id FROM questions WHERE topic_id = ? ORDER BY id",
                (topic_ids[(subject_name, featured_topic)],),
            )
            topic_q_ids = [r["id"] for r in topic_q_ids]
            if topic_q_ids:
                make_quiz(
                    f"{featured_topic} — Topic Test",
                    f"Focused practice test on {featured_topic} ({subject_name}).",
                    subject_ids[subject_name], topic_ids[(subject_name, featured_topic)], 0,
                    max(10, len(topic_q_ids) * 3),
                    topic_q_ids,
                )

    # Full JEE mock test mixing all three subjects
    mock_question_ids = []
    for subject_name in SYLLABUS:
        mock_question_ids.extend(all_by_subject[subject_name][:5])
    if mock_question_ids:
        make_quiz(
            "JEE Main Mock Test 1",
            "A full-length mock test with questions from Physics, Chemistry and Mathematics.",
            None, None, 1, 60, mock_question_ids,
        )

    print("Sample quizzes created: subject practice sets, a featured topic test per subject, "
          "and one full JEE mock test.")


if __name__ == "__main__":
    seed()
    print("\nJEE data seeding complete. Start the app with: python app.py")
