# POO_ServeurC2_2025_26_Derminassian_Cazals

# 🛡️Projet Serveur C2 (REDTEAM) 

Le but du projet est de développer en Python 3 une preuve de concept d’un serveur C2 et de clients « cibles » dans le but d’apprendre les principes d’architecture d’un système C2 (communication, gestion d’agents, exécution de commandes)

---
# 🔐 Fonctionnalités

✅ Écoute TCP et acceptation de connexions
✅Identification basique de la cible
✅Gestion multi-cibles (threads)
✅Envoi de commandes et réception de résultats
✅Commande de terminaison côté cible

---
# 🗂️Structure du projet

  POO_ServeurC2_2025_26_noms_binome/
  ├─ server/                 # code serveur (POC)
  │  └─ server.py
  ├─ cible/                  # code client (POC)
  │  └─ cible.py
  ├─ README.md               # (vous lisez ceci)
  └─ LICENSE
---
#⚙️Technologies utilisées

    Python 3
    socket et ssl (librairies standards)
    threading
    Architecture orientée objet
