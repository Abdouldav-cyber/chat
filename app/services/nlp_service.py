"""
Service NLP avec SpaCy pour le Chatbot RH
Détection d'intentions et extraction d'entités
"""
import spacy
from typing import Dict, List, Tuple, Optional
import re
from app.database.connection import execute_query

# Chargement du modèle SpaCy français
try:
    nlp = spacy.load("fr_core_news_md")
except OSError:
    # Si le modèle n'est pas installé, utiliser le petit modèle
    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        nlp = None
        print("⚠️ Modèle SpaCy non trouvé. Exécutez: python -m spacy download fr_core_news_md")


class NLPService:
    """Service de traitement du langage naturel pour le chatbot RH"""
    
    def __init__(self):
        self.intents_cache = []
        try:
            self._load_intents()
        except Exception as e:
            print(f"⚠️ Impossible de charger les intentions: {e}")
            print("   Veuillez initialiser la base de données via /init-db")
    
    def _load_intents(self):
        """Charge les intentions depuis la base de données"""
        query = """
            SELECT intent_name, categorie, reponse, mots_cles, priorite 
            FROM intents 
            WHERE actif = TRUE 
            ORDER BY priorite DESC
        """
        self.intents_cache = execute_query(query, fetch_all=True) or []
    
    def reload_intents(self):
        """Recharge les intentions (utile après modification)"""
        self._load_intents()
    
    def preprocess_text(self, text: str) -> str:
        """
        Prétraitement du texte utilisateur
        - Mise en minuscules
        - Suppression des accents problématiques
        - Normalisation des espaces
        """
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def extract_entities(self, text: str) -> Dict:
        """
        Extrait les entités nommées du texte
        - Dates
        - Montants
        - Durées
        """
        entities = {
            "dates": [],
            "montants": [],
            "durees": [],
            "personnes": []
        }
        
        if nlp is None:
            return entities
        
        doc = nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "DATE":
                entities["dates"].append(ent.text)
            elif ent.label_ == "MONEY":
                entities["montants"].append(ent.text)
            elif ent.label_ == "PER":
                entities["personnes"].append(ent.text)
        
        # Extraction manuelle des durées (ex: "5 jours", "2 semaines")
        duree_pattern = r'(\d+)\s*(jour|jours|semaine|semaines|mois|an|ans)'
        durees = re.findall(duree_pattern, text.lower())
        entities["durees"] = [f"{d[0]} {d[1]}" for d in durees]
        
        # Extraction des dates au format JJ/MM/AAAA
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        dates_format = re.findall(date_pattern, text)
        entities["dates"].extend(dates_format)
        
        return entities
    
    def calculate_similarity(self, text: str, keywords: List[str]) -> float:
        """
        Calcule la similarité entre le texte et une liste de mots-clés
        Utilise une combinaison de correspondance exacte et de similarité sémantique
        """
        if not keywords:
            return 0.0
        
        text_lower = self.preprocess_text(text)
        text_words = set(text_lower.split())
        
        # Score basé sur les mots-clés présents
        matches = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Correspondance exacte ou partielle
            if keyword_lower in text_lower:
                matches += 2  # Bonus pour correspondance exacte dans le texte
            elif any(keyword_lower in word or word in keyword_lower for word in text_words):
                matches += 1  # Correspondance partielle
        
        # Normalisation du score
        base_score = matches / (len(keywords) * 2) if keywords else 0
        
        # Bonus avec SpaCy si disponible
        if nlp is not None and matches > 0:
            doc_text = nlp(text_lower)
            doc_keywords = nlp(" ".join(keywords))
            
            if doc_text.vector_norm and doc_keywords.vector_norm:
                semantic_score = doc_text.similarity(doc_keywords)
                # Combinaison des scores
                return min(1.0, (base_score * 0.6) + (semantic_score * 0.4))
        
        return min(1.0, base_score)
    
    def detect_intent(self, text: str) -> Tuple[str, float, Dict]:
        """
        Détecte l'intention principale du message
        
        Returns:
            Tuple (intent_name, confidence_score, entities)
        """
        if not self.intents_cache:
            self._load_intents()
        
        text_processed = self.preprocess_text(text)
        entities = self.extract_entities(text)
        
        best_intent = "unknown"
        best_score = 0.0
        
        for intent in self.intents_cache:
            keywords = intent.get('mots_cles') or []
            score = self.calculate_similarity(text_processed, keywords)
            
            # Ajuster le score avec la priorité
            priority_bonus = intent.get('priorite', 0) * 0.01
            adjusted_score = score + priority_bonus
            
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_intent = intent['intent_name']
        
        # Seuil de confiance minimum
        if best_score < 0.15:
            best_intent = "unknown"
            best_score = 0.0
        
        return best_intent, min(1.0, best_score), entities
    
    def get_response(self, intent: str) -> str:
        """
        Récupère la réponse associée à une intention
        """
        if intent == "unknown":
            return ("Je ne suis pas sûr de comprendre votre question. "
                   "Pouvez-vous reformuler ? Vous pouvez me demander de l'aide "
                   "sur les congés, la paie, les avantages sociaux, ou faire une demande.")
        
        query = "SELECT reponse FROM intents WHERE intent_name = %s AND actif = TRUE"
        result = execute_query(query, (intent,), fetch_one=True)
        
        if result:
            return result['reponse']
        
        return "Je n'ai pas trouvé de réponse à cette question. Contactez le service RH."
    
    def process_message(self, message: str, employe_id: Optional[int] = None, 
                       session_id: Optional[str] = None) -> Dict:
        """
        Traite un message utilisateur complet
        
        Args:
            message: Le message de l'utilisateur
            employe_id: L'ID de l'employé (optionnel)
            session_id: L'ID de session (optionnel)
        
        Returns:
            Dict avec intent, réponse, entités et score de confiance
        """
        intent, confidence, entities = self.detect_intent(message)
        response = self.get_response(intent)
        
        # Personnalisation de la réponse si l'employé est identifié
        if employe_id and intent == "conge_solde":
            solde = self._get_solde_conges(employe_id)
            if solde is not None:
                response = f"Votre solde de congés actuel est de {solde} jours. {response}"
        
        # Enregistrement de la conversation
        self._log_conversation(
            employe_id=employe_id,
            session_id=session_id,
            message=message,
            intent=intent,
            response=response,
            confidence=confidence
        )
        
        result = {
            "intent": intent,
            "answer": response,
            "confidence": round(confidence, 4),
            "entities": entities,
            "suggestions": self._get_suggestions(intent)
        }
        
        return result
    
    def _get_solde_conges(self, employe_id: int) -> Optional[float]:
        """Récupère le solde de congés d'un employé"""
        query = "SELECT solde_conges FROM employes WHERE id = %s"
        result = execute_query(query, (employe_id,), fetch_one=True)
        return result['solde_conges'] if result else None
    
    def _log_conversation(self, employe_id, session_id, message, intent, response, confidence):
        """Enregistre la conversation dans la base de données"""
        query = """
            INSERT INTO conversations 
            (employe_id, session_id, message_utilisateur, intent_detecte, reponse_bot, score_confiance)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            execute_query(
                query, 
                (employe_id, session_id, message, intent, response, confidence),
                commit=True
            )
        except Exception as e:
            print(f"Erreur log conversation: {e}")
    
    def _get_suggestions(self, intent: str) -> List[str]:
        """Retourne des suggestions basées sur l'intention détectée"""
        suggestions_map = {
            "conge_solde": ["Comment demander un congé ?", "Quels types de congés ?"],
            "conge_demande": ["Voir mon solde de congés", "Types de congés disponibles"],
            "paie_date": ["Voir ma fiche de paie", "Quelles sont mes primes ?"],
            "paie_fiche": ["Date du prochain virement", "Demander une attestation"],
            "avantage_sante": ["Transport", "Tickets restaurant", "Formation"],
            "unknown": ["Congés", "Paie", "Avantages sociaux", "Faire une demande"],
            "salutation": ["Solde de congés", "Date de paie", "Mes avantages"],
            "aide": ["Demander un congé", "Ma fiche de paie", "Mes avantages"]
        }
        return suggestions_map.get(intent, ["Aide", "Contacter RH"])


# Instance singleton du service
nlp_service = NLPService()
