"""Pack de démarrage RAG : problèmes IT courants (Windows, Office, réseau, matériel).

Base de dépannage générique, à enrichir/adapter par le client. Importable en un
clic depuis la page Connaissances. Chaque entrée : titre + procédure concise.
"""

STARTER_PACK: list[dict] = [
    # ---- Windows ----
    {"source": "Windows", "title": "Windows lent au démarrage",
     "content": "Désactiver les programmes de démarrage inutiles (Gestionnaire des tâches > Démarrage). "
                "Vérifier l'espace disque (> 15% libre). Lancer `sfc /scannow` puis "
                "`DISM /Online /Cleanup-Image /RestoreHealth`. Vérifier les mises à jour Windows."},
    {"source": "Windows", "title": "Écran bleu (BSOD)",
     "content": "Noter le code d'arrêt (ex. MEMORY_MANAGEMENT, IRQL_NOT_LESS_OR_EQUAL). "
                "Mettre à jour les pilotes (surtout carte graphique/chipset). Tester la RAM avec "
                "mdsched.exe. Analyser le minidump (C:\\Windows\\Minidump) avec BlueScreenView. "
                "Désinstaller la dernière mise à jour si le problème est récent."},
    {"source": "Windows", "title": "Windows Update bloqué / en erreur",
     "content": "Exécuter l'utilitaire de résolution des problèmes Windows Update. Arrêter les services "
                "wuauserv et bits, renommer C:\\Windows\\SoftwareDistribution, redémarrer les services. "
                "Commande : `net stop wuauserv & net stop bits & ren %systemroot%\\SoftwareDistribution SD.old & "
                "net start wuauserv & net start bits`."},
    {"source": "Windows", "title": "Imprimante ne répond plus",
     "content": "Redémarrer le service Spouleur d'impression (services.msc > Spouleur d'impression > Redémarrer). "
                "Vider la file : arrêter le spouleur, supprimer C:\\Windows\\System32\\spool\\PRINTERS\\*, redémarrer. "
                "Vérifier la connectivité réseau/USB et réinstaller le pilote si besoin."},
    {"source": "Windows", "title": "Profil utilisateur temporaire",
     "content": "Symptôme : « Vous êtes connecté avec un profil temporaire ». Cause : profil corrompu. "
                "Solution : regedit > HKLM\\...\\ProfileList, supprimer la clé .bak en double après sauvegarde, "
                "vérifier les droits sur C:\\Users\\<user>. Redémarrer."},
    {"source": "Windows", "title": "Espace disque C: saturé",
     "content": "Nettoyage de disque (cleanmgr) + « Nettoyer les fichiers système ». Supprimer les points de "
                "restauration anciens. Vider %temp%. Déplacer OneDrive/Téléchargements. Vérifier "
                "C:\\Windows\\Temp et les fichiers de mise à jour Windows."},

    # ---- Microsoft Office / 365 ----
    {"source": "Office", "title": "Office ne s'ouvre pas / plante au démarrage",
     "content": "Démarrer en mode sans échec (ex. `excel /safe`). Désactiver les compléments (COM Add-ins). "
                "Réparer Office : Panneau de configuration > Programmes > Microsoft 365 > Modifier > "
                "Réparation rapide puis Réparation en ligne. Vérifier les mises à jour Office."},
    {"source": "Office", "title": "Outlook ne se connecte pas / boîte bloquée",
     "content": "Vérifier la connexion réseau et l'état du service (portal.office.com). Recréer le profil Outlook "
                "(Panneau de config > Mail > Afficher les profils). Réparer le fichier de données (.ost/.pst) avec "
                "scanpst.exe. Vider le cache d'identification Windows (Gestionnaire d'identification)."},
    {"source": "Office", "title": "Fichier Excel/Word corrompu",
     "content": "Ouvrir avec « Ouvrir et réparer » (Fichier > Ouvrir > flèche du bouton Ouvrir). Récupérer une "
                "version précédente (clic droit > Versions précédentes, ou historique OneDrive/SharePoint). "
                "Tester l'ouverture sur un autre poste pour isoler un problème local."},
    {"source": "Office", "title": "Activation Office échoue",
     "content": "Vérifier la licence associée au compte (account.microsoft.com). Se déconnecter/reconnecter dans "
                "un app Office (Fichier > Compte). Lancer l'assistant de support et récupération (SaRA). "
                "En volume : vérifier le KMS/ADBA avec `cscript ospp.vbs /dstatus`."},
    {"source": "Office", "title": "OneDrive ne synchronise plus",
     "content": "Vérifier l'icône OneDrive (pause ?). Se déconnecter/reconnecter le compte. Réinitialiser : "
                "`%localappdata%\\Microsoft\\OneDrive\\onedrive.exe /reset`. Vérifier l'espace disponible et les "
                "chemins > 260 caractères. Contrôler les conflits de fichiers."},

    # ---- Réseau ----
    {"source": "Réseau", "title": "Pas d'accès Internet sur un poste",
     "content": "Vérifier le câble/Wi-Fi et l'adresse IP (`ipconfig /all` : IP en 169.254 = pas de DHCP). "
                "Renouveler : `ipconfig /release & ipconfig /renew`. Vider le cache DNS : `ipconfig /flushdns`. "
                "Tester `ping 8.8.8.8` (réseau) puis `ping google.com` (DNS). Vérifier passerelle et pare-feu."},
    {"source": "Réseau", "title": "Ping échoue vers un poste Windows",
     "content": "Windows bloque l'ICMP par défaut. Autoriser : `New-NetFirewallRule -DisplayName 'ICMP' "
                "-Protocol ICMPv4 -IcmpType 8 -Direction Inbound -Action Allow` (PowerShell admin). "
                "Vérifier que le poste est allumé et sur le même sous-réseau."},
    {"source": "Réseau", "title": "Lecteur réseau inaccessible",
     "content": "Vérifier la connectivité au serveur (`ping`, `\\\\serveur`). Reconnecter le lecteur "
                "(`net use Z: \\\\serveur\\partage /persistent:yes`). Vérifier les identifiants (Gestionnaire "
                "d'identification) et les permissions NTFS/partage côté serveur."},

    # ---- Matériel / divers ----
    {"source": "Matériel", "title": "PC ne s'allume pas",
     "content": "Vérifier l'alimentation (câble, prise, interrupteur PSU). Tester un autre câble/prise. "
                "Débrancher les périphériques USB. Réinitialiser l'alimentation (maintenir bouton power 15 s "
                "débranché). Vérifier les voyants/bips de la carte mère (codes POST)."},
    {"source": "Matériel", "title": "Pas de son",
     "content": "Vérifier le périphérique de sortie par défaut (clic droit icône son > Paramètres). Mettre à jour "
                "le pilote audio. Redémarrer le service Windows Audio (services.msc). Tester un casque pour isoler "
                "les haut-parleurs. Vérifier le volume par application (Mélangeur)."},
]
