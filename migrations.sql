-- =============================================
-- Chatbot RH - Fonction Publique
-- Migrations PostgreSQL
-- =============================================

-- Création de la base de données (exécuter séparément si nécessaire)
-- CREATE DATABASE botrh;

-- Table des employés
CREATE TABLE IF NOT EXISTS employes (
    id SERIAL PRIMARY KEY,
    matricule VARCHAR(50) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    departement VARCHAR(100),
    poste VARCHAR(100),
    date_embauche DATE,
    solde_conges DECIMAL(5,2) DEFAULT 30.00,
    mot_de_passe VARCHAR(255),
    role VARCHAR(20) DEFAULT 'employe', -- employe, gestionnaire, admin
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des intentions du chatbot
CREATE TABLE IF NOT EXISTS intents (
    id SERIAL PRIMARY KEY,
    intent_name VARCHAR(100) UNIQUE NOT NULL,
    categorie VARCHAR(50), -- conges, paie, avantages, general
    description TEXT,
    reponse TEXT NOT NULL,
    mots_cles TEXT[], -- Array de mots-clés pour le matching
    priorite INTEGER DEFAULT 0,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des demandes (congés, remboursements, etc.)
CREATE TABLE IF NOT EXISTS demandes (
    id SERIAL PRIMARY KEY,
    employe_id INTEGER REFERENCES employes(id) ON DELETE CASCADE,
    type_demande VARCHAR(50) NOT NULL, -- conge, remboursement, attestation, autre
    sous_type VARCHAR(50), -- conge_annuel, conge_maladie, remboursement_transport, etc.
    date_debut DATE,
    date_fin DATE,
    nb_jours DECIMAL(5,2),
    montant DECIMAL(10,2),
    motif TEXT,
    justificatif_path VARCHAR(500),
    statut VARCHAR(30) DEFAULT 'en_attente', -- en_attente, approuve, refuse, annule
    commentaire_gestionnaire TEXT,
    traite_par INTEGER REFERENCES employes(id),
    date_traitement TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des conversations du chatbot
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    employe_id INTEGER REFERENCES employes(id) ON DELETE SET NULL,
    session_id VARCHAR(100),
    message_utilisateur TEXT NOT NULL,
    intent_detecte VARCHAR(100),
    reponse_bot TEXT NOT NULL,
    score_confiance DECIMAL(5,4),
    feedback INTEGER, -- 1 positif, -1 négatif, NULL pas de feedback
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    employe_id INTEGER REFERENCES employes(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type_notification VARCHAR(50), -- echeance, demande, info
    lue BOOLEAN DEFAULT FALSE,
    lien VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des échéances RH
CREATE TABLE IF NOT EXISTS echeances (
    id SERIAL PRIMARY KEY,
    employe_id INTEGER REFERENCES employes(id) ON DELETE CASCADE,
    type_echeance VARCHAR(100) NOT NULL, -- fin_periode_essai, anniversaire, visite_medicale, etc.
    date_echeance DATE NOT NULL,
    description TEXT,
    notification_envoyee BOOLEAN DEFAULT FALSE,
    jours_avant_notification INTEGER DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table de la paie (informations de base)
CREATE TABLE IF NOT EXISTS fiches_paie (
    id SERIAL PRIMARY KEY,
    employe_id INTEGER REFERENCES employes(id) ON DELETE CASCADE,
    mois INTEGER NOT NULL,
    annee INTEGER NOT NULL,
    salaire_brut DECIMAL(12,2),
    salaire_net DECIMAL(12,2),
    primes DECIMAL(12,2) DEFAULT 0,
    deductions DECIMAL(12,2) DEFAULT 0,
    date_virement DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employe_id, mois, annee)
);

-- Table des avantages sociaux
CREATE TABLE IF NOT EXISTS avantages (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    categorie VARCHAR(50), -- sante, transport, restauration, formation
    conditions TEXT,
    montant_ou_taux VARCHAR(100),
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table de liaison employés-avantages
CREATE TABLE IF NOT EXISTS employes_avantages (
    id SERIAL PRIMARY KEY,
    employe_id INTEGER REFERENCES employes(id) ON DELETE CASCADE,
    avantage_id INTEGER REFERENCES avantages(id) ON DELETE CASCADE,
    date_attribution DATE,
    date_fin DATE,
    actif BOOLEAN DEFAULT TRUE,
    UNIQUE(employe_id, avantage_id)
);

-- =============================================
-- Données initiales
-- =============================================

-- Intents pour le chatbot
INSERT INTO intents (intent_name, categorie, reponse, mots_cles, priorite) VALUES
-- Congés
('conge_solde', 'conges', 'Votre solde de congés actuel est affiché dans votre espace personnel. En règle générale, vous cumulez 2,5 jours par mois travaillé, soit 30 jours par an.', ARRAY['solde', 'congés', 'reste', 'jours', 'disponible'], 10),
('conge_demande', 'conges', 'Pour demander un congé, utilisez le bouton "Nouvelle demande" et sélectionnez "Congé". Précisez les dates et le motif. Votre gestionnaire RH sera notifié automatiquement.', ARRAY['demander', 'poser', 'congé', 'vacances', 'absent'], 10),
('conge_types', 'conges', 'Les types de congés disponibles sont : congé annuel, congé maladie (avec justificatif), congé maternité/paternité, congé exceptionnel (mariage, décès, naissance), et congé sans solde.', ARRAY['type', 'congé', 'maladie', 'maternité', 'paternité', 'exceptionnel'], 8),
('conge_annulation', 'conges', 'Pour annuler une demande de congé en attente, allez dans "Mes demandes" et cliquez sur "Annuler". Si le congé est déjà approuvé, contactez votre gestionnaire RH.', ARRAY['annuler', 'supprimer', 'congé', 'demande'], 7),

-- Paie
('paie_date', 'paie', 'Les salaires sont virés le 27 de chaque mois. Si le 27 tombe un week-end ou jour férié, le virement est effectué le jour ouvré précédent.', ARRAY['salaire', 'virement', 'paie', 'date', 'quand'], 10),
('paie_fiche', 'paie', 'Vos fiches de paie sont accessibles dans votre espace personnel, section "Mes fiches de paie". Vous pouvez les télécharger en PDF.', ARRAY['fiche', 'paie', 'bulletin', 'télécharger'], 9),
('paie_prime', 'paie', 'Les primes varient selon votre statut et ancienneté. Consultez votre convention collective ou contactez le service RH pour plus de détails sur les primes auxquelles vous avez droit.', ARRAY['prime', 'bonus', 'indemnité', 'gratification'], 8),
('paie_augmentation', 'paie', 'Les augmentations sont généralement décidées lors des entretiens annuels ou selon les grilles indiciaires de la fonction publique. Consultez votre gestionnaire RH pour plus d''informations.', ARRAY['augmentation', 'hausse', 'salaire', 'évolution'], 7),

-- Avantages sociaux
('avantage_sante', 'avantages', 'Vous bénéficiez d''une mutuelle santé prise en charge à 50% par l''employeur. Les détails de couverture sont disponibles dans votre espace personnel.', ARRAY['mutuelle', 'santé', 'médical', 'remboursement', 'soins'], 9),
('avantage_transport', 'avantages', 'Le remboursement transport couvre 50% de votre abonnement de transport en commun. Soumettez votre justificatif via une demande de remboursement.', ARRAY['transport', 'navigo', 'abonnement', 'métro', 'bus', 'train'], 9),
('avantage_restaurant', 'avantages', 'Les tickets restaurant ont une valeur faciale de 9€, dont 5,40€ pris en charge par l''employeur. Ils sont crédités mensuellement.', ARRAY['ticket', 'restaurant', 'repas', 'cantine', 'déjeuner'], 8),
('avantage_formation', 'avantages', 'Vous disposez d''un droit à la formation professionnelle. Consultez le catalogue de formations et faites votre demande via le portail RH.', ARRAY['formation', 'cours', 'apprendre', 'compétence', 'CPF'], 8),

-- Remboursements
('remboursement_demande', 'remboursements', 'Pour demander un remboursement, cliquez sur "Nouvelle demande", sélectionnez "Remboursement", précisez le type (transport, frais professionnels) et joignez vos justificatifs.', ARRAY['remboursement', 'frais', 'rembourser', 'facture'], 10),
('remboursement_statut', 'remboursements', 'Le statut de vos demandes de remboursement est visible dans "Mes demandes". Le délai de traitement est généralement de 5 à 10 jours ouvrés.', ARRAY['statut', 'suivi', 'remboursement', 'où en est'], 8),

-- Attestations
('attestation_travail', 'attestations', 'Pour obtenir une attestation de travail, faites une demande via "Nouvelle demande" > "Attestation". Elle sera générée sous 48h ouvrées.', ARRAY['attestation', 'travail', 'employeur', 'certificat'], 9),
('attestation_salaire', 'attestations', 'L''attestation de salaire peut être demandée pour un prêt bancaire ou une location. Précisez l''usage dans votre demande.', ARRAY['attestation', 'salaire', 'banque', 'prêt', 'location'], 8),

-- Général
('salutation', 'general', 'Bonjour ! Je suis votre assistant RH virtuel. Comment puis-je vous aider aujourd''hui ? Vous pouvez me poser des questions sur les congés, la paie, les avantages sociaux, ou faire une demande.', ARRAY['bonjour', 'salut', 'hello', 'coucou', 'bonsoir'], 5),
('remerciement', 'general', 'Je vous en prie ! N''hésitez pas si vous avez d''autres questions. Je suis là pour vous aider.', ARRAY['merci', 'thanks', 'parfait', 'super', 'génial'], 5),
('aide', 'general', 'Je peux vous aider avec : 📅 Congés (solde, demande, types) | 💰 Paie (dates, fiches, primes) | 🎁 Avantages (mutuelle, transport, restaurant) | 📝 Demandes (remboursements, attestations). Que souhaitez-vous savoir ?', ARRAY['aide', 'help', 'quoi', 'comment', 'possible'], 5),
('contact_rh', 'general', 'Pour contacter le service RH directement : email rh@fonction-publique.fr ou téléphone 01 XX XX XX XX (du lundi au vendredi, 9h-17h).', ARRAY['contact', 'joindre', 'téléphone', 'email', 'RH', 'humain'], 6)

ON CONFLICT (intent_name) DO UPDATE SET
    reponse = EXCLUDED.reponse,
    mots_cles = EXCLUDED.mots_cles;

-- Avantages sociaux par défaut
INSERT INTO avantages (nom, description, categorie, conditions, montant_ou_taux) VALUES
('Mutuelle santé', 'Complémentaire santé obligatoire', 'sante', 'Tous les employés', '50% pris en charge'),
('Transport', 'Remboursement abonnement transport', 'transport', 'Sur justificatif', '50% du Pass Navigo'),
('Tickets restaurant', 'Titres restaurant journaliers', 'restauration', 'Par jour travaillé', '9€ (5,40€ employeur)'),
('Formation professionnelle', 'Accès aux formations', 'formation', 'Selon plan de formation', 'Variable')
ON CONFLICT DO NOTHING;

-- Employé de test (gestionnaire RH)
INSERT INTO employes (matricule, nom, prenom, email, departement, poste, role, mot_de_passe)
VALUES ('RH001', 'Admin', 'RH', 'admin@rh.fr', 'Ressources Humaines', 'Gestionnaire RH', 'gestionnaire', 
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4W0VpMPgIgxGKJ.G') -- mot de passe: admin123
ON CONFLICT (email) DO NOTHING;

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_demandes_employe ON demandes(employe_id);
CREATE INDEX IF NOT EXISTS idx_demandes_statut ON demandes(statut);
CREATE INDEX IF NOT EXISTS idx_notifications_employe ON notifications(employe_id);
CREATE INDEX IF NOT EXISTS idx_echeances_date ON echeances(date_echeance);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
