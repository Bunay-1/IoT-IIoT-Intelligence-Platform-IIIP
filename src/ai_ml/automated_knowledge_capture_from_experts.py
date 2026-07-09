from dataclasses import dataclass, field
from typing import List, Set
import spacy

@dataclass(frozen=True)
class KnowledgeTriple:
    """Represents a structured fact (Subject-Predicate-Object)."""
    subject: str
    predicate: str
    object: str

@dataclass(frozen=True)
class HeuristicRule:
    """Represents a simple IF-THEN rule."""
    condition: str
    action: str


class KnowledgeBase:
    """A simple container for storing and managing extracted knowledge."""
    def __init__(self):
        self.triples: Set[KnowledgeTriple] = set()
        self.rules: Set[HeuristicRule] = set()

    def add_triple(self, triple: KnowledgeTriple):
        self.triples.add(triple)

    def add_rule(self, rule: HeuristicRule):
        self.rules.add(rule)

    def display(self):
        """Prints the contents of the knowledge base."""
        print("\n--- Consolidated Knowledge Base ---")
        if not self.triples and not self.rules:
            print("Knowledge base is empty.")
            return

        if self.triples:
            print(f"\nFound {len(self.triples)} unique facts:")
            for t in sorted(list(self.triples), key=lambda x: x.subject):
                print(f"  - {t.subject} {t.predicate} {t.object}")

        if self.rules:
            print(f"\nFound {len(self.rules)} unique rules:")
            for r in sorted(list(self.rules), key=lambda x: x.condition):
                print(f"  - IF '{r.condition}' THEN '{r.action}'")


class AutomatedKnowledgeCaptureFromExperts:
    def __init__(self, expert_interviews: List[str]):
        self.expert_interviews = expert_interviews
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading 'en_core_web_sm' model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def capture_knowledge(self):
        """Processes all interviews and returns the extracted knowledge base."""
        print("Starting knowledge capture from expert interviews...")
        knowledge_base = KnowledgeBase()
        for i, interview_text in enumerate(self.expert_interviews):
            print(f"\n--- Analyzing Interview #{i+1} ---")
            triples, rules = self.analyze_single_interview(interview_text)

            if triples:
                print(f"  Found {len(triples)} potential knowledge triples:")
                for triple in triples:
                    knowledge_base.add_triple(triple)
                    print(f"    - Fact: {triple.subject} -> {triple.predicate} -> {triple.object}")

            if rules:
                print(f"  Found {len(rules)} potential heuristic rules:")
                for rule in rules:
                    knowledge_base.add_rule(rule)
                    print(f"    - Rule: IF '{rule.condition}' THEN '{rule.action}'")

        print("\n--- Knowledge Capture Complete ---")
        return knowledge_base

    def analyze_single_interview(self, interview_text: str) -> (List[KnowledgeTriple], List[HeuristicRule]):
        """Analyzes a single interview text to extract knowledge."""
        doc = self.nlp(interview_text)

        triples = []
        rules = []

        # Find SVO triples
        for possible_subject in doc:
            if "subj" in possible_subject.dep_ and possible_subject.head.pos_ == "VERB":
                subject = possible_subject
                predicate = subject.head
                for child in predicate.children:
                    if "obj" in child.dep_ or "attr" in child.dep_:
                        obj = child
                        triples.append(KnowledgeTriple(subject.text, predicate.text, obj.text))
                        break

        # Find IF-THEN rules by sentence analysis
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if "if" in sent_text and "then" in sent_text:
                parts = sent.text.split(" then ")
                if len(parts) == 2:
                    condition = parts[0].replace("if", "").replace(",", "").strip()
                    action = parts[1].strip(" .")
                    rules.append(HeuristicRule(condition, action))

        return triples, rules


if __name__ == '__main__':
    # Sample expert interview transcripts
    expert_interviews = [
        "In our system, high CPU usage often causes performance degradation. We've also seen that memory leaks are a common problem.",
        "A key takeaway is that the database connection pool definitely impacts response time. Also, if the transaction volume exceeds 1000 TPS, then we must scale up the read replicas.",
        "From my experience, if the API latency is over 300ms, then an alert should be triggered immediately. It's a critical indicator.",
        "We have a rule: if a user has more than 5 failed login attempts, then their account is temporarily locked. This is a standard security measure. High CPU usage also causes performance degradation, which is something the other team mentioned."
    ]

    print("--- Initializing Automated Knowledge Capture Engine ---")
    # 1. Initialize the capture engine with the interview texts
    capture_engine = AutomatedKnowledgeCaptureFromExperts(expert_interviews)

    # 2. Run the knowledge capture process
    # This will analyze the texts and populate a knowledge base
    final_knowledge_base = capture_engine.capture_knowledge()

    # 3. Display the consolidated and deduplicated knowledge
    final_knowledge_base.display()
