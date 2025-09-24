## 🛡️Projet Serveur C2 (REDTEAM) POO_ServeurC2_2025_26_Derminassian_Cazals

Le but du projet est de développer en Python 3 une preuve de concept d’un serveur C2 et de clients « cibles » dans le but d’apprendre les principes d’architecture d’un système C2 (communication, gestion d’agents, exécution de commandes)

---
## 🔐 Fonctionnalités

- ✅Écoute TCP et acceptation de connexions
- ✅Identification basique de la cible
- ✅Gestion multi-cibles (threads)
- ✅Envoi de commandes et réception de résultats
- ✅Commande de terminaison côté cible

---
## 🗂️Structure du projet

```
POO_ServeurC2_2025_26_Derminassian_Cazals/
├── serveur/
│   └── serveur.py
├── client/
│   └── client.py
└── README.md
```
---
## ⚙️Technologies utilisées

- ***Python 3***
- ***Socket***
-  ***Threading***
- ***Architecture orientée objet***

## 📥 Prérequis

- Python 3

## 🚀 Lancement
📡 Lancer le serveur (sur la VM serveur) :

python3 server.py 

💻 Lancer un client (sur la VM client) :

python3 client.py 
