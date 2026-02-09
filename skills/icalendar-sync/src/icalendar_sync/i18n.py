#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n - Internationalization support
Supports: English, Spanish, French, German, Italian

@author: Black_Temple
@version: 2.3.0
"""

import os
import locale
from typing import Dict

# Supported languages
SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'it']

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'en': {
        # Setup
        'setup_title': '🔧 iCalendar Sync Setup',
        'setup_intro': 'To use iCalendar Sync, you need to configure your iCloud credentials.',
        'setup_warning': '⚠️  Use an App-Specific Password, NOT your regular Apple ID password.',
        'setup_url': 'Get it from: https://appleid.apple.com -> Sign-In & Security -> App-Specific Passwords',
        'email_prompt': '📧 iCloud Email: ',
        'password_prompt': '🔑 App-Specific Password (xxxx-xxxx-xxxx-xxxx): ',
        'email_empty': '❌ Email cannot be empty',
        'password_empty': '❌ Password cannot be empty',
        'invalid_email': '❌ Invalid email format',
        'continue_anyway': 'Continue anyway? (y/n): ',
        'password_unusual': '⚠️  Password format looks unusual',
        'are_you_sure': 'Are you sure this is correct? (y/n): ',
        'setup_cancelled': 'Setup cancelled',
        'credentials_saved_keyring': '✅ Credentials saved securely to system keyring',
        'keyring_fallback': '⚠️  Could not access system keyring, falling back to .env file',
        'credentials_saved_file': '✅ Configuration saved securely to {path}',
        'ready_to_use': '🚀 You can now use iCalendar Sync!',
        
        # Calendar operations
        'available_calendars': '📅 Available Calendars ({count}):',
        'events_in_calendar': '📋 Events in \'{name}\' ({count} found):',
        'event_created': '✅ Event \'{summary}\' created successfully',
        'event_deleted': '🗑️  Event deleted successfully',
        
        # Errors
        'error_required_packages': '❌ Required packages not installed: {error}',
        'error_run_install': 'Run: pip install -r requirements.txt',
        'error_credentials_missing': '❌ iCloud credentials not configured',
        'error_auth_failed': '❌ Authentication failed: Invalid credentials',
        'error_network': '❌ Network error',
        'error_caldav': '❌ CalDAV error',
        'error_unexpected': '❌ Unexpected error: {type}',
        'error_calendars_not_found': '❌ Calendars not found',
        'error_calendar_not_found': '❌ Calendar \'{name}\' not found',
        'error_events': '❌ Error getting events',
        'error_listing_calendars': '❌ Error listing calendars',
        'error_invalid_calendar_name': '❌ Invalid calendar name',
        'error_days_range': '❌ days_ahead must be between {min} and {max}',
        'error_missing_fields': '❌ Missing required fields: {fields}',
        'error_dtstart_type': '❌ dtstart must be a datetime object',
        'error_dtend_type': '❌ dtend must be a datetime object',
        'error_time_range': '❌ Event end time must be after start time',
        'error_creating_event': '❌ Error creating event',
        'error_event_not_found': '❌ Event or calendar not found',
        'error_deleting_event': '❌ Error deleting event',
        'error_invalid_uid': '❌ Valid event UID required',
        'error_uid_too_long': '❌ Invalid event UID (too long)',
        'error_calendar_required': '❌ Calendar name required',
        'error_json_required': '❌ Calendar and JSON data required',
        'error_json_read': '❌ Could not read JSON file',
        'error_json_too_large': '❌ JSON data too large',
        'error_invalid_json': '❌ Invalid JSON: {error}',
        'error_invalid_datetime': '❌ Invalid datetime format: {error}',
        'error_uid_required': '❌ Calendar and event UID required',
        
        # Warnings
        'warning_conflicts': '⚠️  Warning: {count} conflicting event(s) found:',
        'warning_conflict_item': '   - {summary} ({start} to {end})',
        'confirm_continue': 'Continue anyway? (y/n): ',
        'creation_cancelled': 'Event creation cancelled',
        
        # Info
        'input_timeout': '⏱️  Input timeout',
        'using_cached_connection': 'Using cached CalDAV connection',
        'connection_successful': 'Successfully connected to iCloud CalDAV',
        'found_calendar': 'Found calendar: {name}',
        'found_event': 'Found event: {summary}',
        'loaded_from_keyring': 'Loaded password from keyring',
    },
    
    'es': {
        # Setup
        'setup_title': '🔧 Configuración de iCalendar Sync',
        'setup_intro': 'Para usar iCalendar Sync, necesitas configurar tus credenciales de iCloud.',
        'setup_warning': '⚠️  Usa una Contraseña Específica de App, NO tu contraseña regular de Apple ID.',
        'setup_url': 'Obténla de: https://appleid.apple.com -> Inicio de sesión y seguridad -> Contraseñas específicas de apps',
        'email_prompt': '📧 Email de iCloud: ',
        'password_prompt': '🔑 Contraseña Específica de App (xxxx-xxxx-xxxx-xxxx): ',
        'email_empty': '❌ El email no puede estar vacío',
        'password_empty': '❌ La contraseña no puede estar vacía',
        'invalid_email': '❌ Formato de email inválido',
        'continue_anyway': '¿Continuar de todos modos? (s/n): ',
        'password_unusual': '⚠️  El formato de contraseña parece inusual',
        'are_you_sure': '¿Estás seguro de que es correcto? (s/n): ',
        'setup_cancelled': 'Configuración cancelada',
        'credentials_saved_keyring': '✅ Credenciales guardadas de forma segura en el llavero del sistema',
        'keyring_fallback': '⚠️  No se pudo acceder al llavero del sistema, usando archivo .env',
        'credentials_saved_file': '✅ Configuración guardada de forma segura en {path}',
        'ready_to_use': '🚀 ¡Ya puedes usar iCalendar Sync!',
        
        # Calendar operations
        'available_calendars': '📅 Calendarios Disponibles ({count}):',
        'events_in_calendar': '📋 Eventos en \'{name}\' ({count} encontrados):',
        'event_created': '✅ Evento \'{summary}\' creado exitosamente',
        'event_deleted': '🗑️  Evento eliminado exitosamente',
        
        # Errors
        'error_required_packages': '❌ Paquetes requeridos no instalados: {error}',
        'error_run_install': 'Ejecuta: pip install -r requirements.txt',
        'error_credentials_missing': '❌ Credenciales de iCloud no configuradas',
        'error_auth_failed': '❌ Autenticación fallida: Credenciales inválidas',
        'error_network': '❌ Error de red',
        'error_caldav': '❌ Error de CalDAV',
        'error_unexpected': '❌ Error inesperado: {type}',
        'error_calendars_not_found': '❌ Calendarios no encontrados',
        'error_calendar_not_found': '❌ Calendario \'{name}\' no encontrado',
        'error_events': '❌ Error obteniendo eventos',
        'error_listing_calendars': '❌ Error listando calendarios',
        'error_invalid_calendar_name': '❌ Nombre de calendario inválido',
        'error_days_range': '❌ days_ahead debe estar entre {min} y {max}',
        'error_missing_fields': '❌ Campos requeridos faltantes: {fields}',
        'error_dtstart_type': '❌ dtstart debe ser un objeto datetime',
        'error_dtend_type': '❌ dtend debe ser un objeto datetime',
        'error_time_range': '❌ La hora de fin del evento debe ser posterior a la de inicio',
        'error_creating_event': '❌ Error creando evento',
        'error_event_not_found': '❌ Evento o calendario no encontrado',
        'error_deleting_event': '❌ Error eliminando evento',
        'error_invalid_uid': '❌ Se requiere un UID de evento válido',
        'error_uid_too_long': '❌ UID de evento inválido (demasiado largo)',
        'error_calendar_required': '❌ Se requiere nombre de calendario',
        'error_json_required': '❌ Se requieren calendario y datos JSON',
        'error_json_read': '❌ No se pudo leer el archivo JSON',
        'error_json_too_large': '❌ Datos JSON demasiado grandes',
        'error_invalid_json': '❌ JSON inválido: {error}',
        'error_invalid_datetime': '❌ Formato de fecha/hora inválido: {error}',
        'error_uid_required': '❌ Se requieren calendario y UID de evento',
        
        # Warnings
        'warning_conflicts': '⚠️  Advertencia: {count} evento(s) en conflicto encontrado(s):',
        'warning_conflict_item': '   - {summary} ({start} a {end})',
        'confirm_continue': '¿Continuar de todos modos? (s/n): ',
        'creation_cancelled': 'Creación de evento cancelada',
        
        # Info
        'input_timeout': '⏱️  Tiempo de espera agotado',
        'using_cached_connection': 'Usando conexión CalDAV en caché',
        'connection_successful': 'Conectado exitosamente a iCloud CalDAV',
        'found_calendar': 'Calendario encontrado: {name}',
        'found_event': 'Evento encontrado: {summary}',
        'loaded_from_keyring': 'Contraseña cargada desde el llavero',
    },
    
    'fr': {
        # Setup
        'setup_title': '🔧 Configuration d\'iCalendar Sync',
        'setup_intro': 'Pour utiliser iCalendar Sync, vous devez configurer vos identifiants iCloud.',
        'setup_warning': '⚠️  Utilisez un Mot de passe spécifique à l\'app, PAS votre mot de passe Apple ID habituel.',
        'setup_url': 'Obtenez-le sur : https://appleid.apple.com -> Connexion et sécurité -> Mots de passe spécifiques',
        'email_prompt': '📧 Email iCloud : ',
        'password_prompt': '🔑 Mot de passe spécifique (xxxx-xxxx-xxxx-xxxx) : ',
        'email_empty': '❌ L\'email ne peut pas être vide',
        'password_empty': '❌ Le mot de passe ne peut pas être vide',
        'invalid_email': '❌ Format d\'email invalide',
        'continue_anyway': 'Continuer quand même ? (o/n) : ',
        'password_unusual': '⚠️  Le format du mot de passe semble inhabituel',
        'are_you_sure': 'Êtes-vous sûr que c\'est correct ? (o/n) : ',
        'setup_cancelled': 'Configuration annulée',
        'credentials_saved_keyring': '✅ Identifiants enregistrés en toute sécurité dans le trousseau système',
        'keyring_fallback': '⚠️  Impossible d\'accéder au trousseau système, utilisation du fichier .env',
        'credentials_saved_file': '✅ Configuration enregistrée en toute sécurité dans {path}',
        'ready_to_use': '🚀 Vous pouvez maintenant utiliser iCalendar Sync !',
        
        # Calendar operations
        'available_calendars': '📅 Calendriers Disponibles ({count}) :',
        'events_in_calendar': '📋 Événements dans \'{name}\' ({count} trouvés) :',
        'event_created': '✅ Événement \'{summary}\' créé avec succès',
        'event_deleted': '🗑️  Événement supprimé avec succès',
        
        # Errors
        'error_required_packages': '❌ Packages requis non installés : {error}',
        'error_run_install': 'Exécutez : pip install -r requirements.txt',
        'error_credentials_missing': '❌ Identifiants iCloud non configurés',
        'error_auth_failed': '❌ Échec de l\'authentification : Identifiants invalides',
        'error_network': '❌ Erreur réseau',
        'error_caldav': '❌ Erreur CalDAV',
        'error_unexpected': '❌ Erreur inattendue : {type}',
        'error_calendars_not_found': '❌ Calendriers non trouvés',
        'error_calendar_not_found': '❌ Calendrier \'{name}\' non trouvé',
        'error_events': '❌ Erreur lors de la récupération des événements',
        'error_listing_calendars': '❌ Erreur lors du listage des calendriers',
        'error_invalid_calendar_name': '❌ Nom de calendrier invalide',
        'error_days_range': '❌ days_ahead doit être entre {min} et {max}',
        'error_missing_fields': '❌ Champs requis manquants : {fields}',
        'error_dtstart_type': '❌ dtstart doit être un objet datetime',
        'error_dtend_type': '❌ dtend doit être un objet datetime',
        'error_time_range': '❌ L\'heure de fin de l\'événement doit être après l\'heure de début',
        'error_creating_event': '❌ Erreur lors de la création de l\'événement',
        'error_event_not_found': '❌ Événement ou calendrier non trouvé',
        'error_deleting_event': '❌ Erreur lors de la suppression de l\'événement',
        'error_invalid_uid': '❌ UID d\'événement valide requis',
        'error_uid_too_long': '❌ UID d\'événement invalide (trop long)',
        'error_calendar_required': '❌ Nom de calendrier requis',
        'error_json_required': '❌ Calendrier et données JSON requis',
        'error_json_read': '❌ Impossible de lire le fichier JSON',
        'error_json_too_large': '❌ Données JSON trop volumineuses',
        'error_invalid_json': '❌ JSON invalide : {error}',
        'error_invalid_datetime': '❌ Format de date/heure invalide : {error}',
        'error_uid_required': '❌ Calendrier et UID d\'événement requis',
        
        # Warnings
        'warning_conflicts': '⚠️  Attention : {count} événement(s) en conflit trouvé(s) :',
        'warning_conflict_item': '   - {summary} ({start} à {end})',
        'confirm_continue': 'Continuer quand même ? (o/n) : ',
        'creation_cancelled': 'Création de l\'événement annulée',
        
        # Info
        'input_timeout': '⏱️  Délai d\'attente dépassé',
        'using_cached_connection': 'Utilisation de la connexion CalDAV en cache',
        'connection_successful': 'Connexion réussie à iCloud CalDAV',
        'found_calendar': 'Calendrier trouvé : {name}',
        'found_event': 'Événement trouvé : {summary}',
        'loaded_from_keyring': 'Mot de passe chargé depuis le trousseau',
    },
    
    'de': {
        # Setup
        'setup_title': '🔧 iCalendar Sync Einrichtung',
        'setup_intro': 'Um iCalendar Sync zu verwenden, müssen Sie Ihre iCloud-Zugangsdaten konfigurieren.',
        'setup_warning': '⚠️  Verwenden Sie ein App-spezifisches Passwort, NICHT Ihr reguläres Apple-ID-Passwort.',
        'setup_url': 'Erhalten Sie es unter: https://appleid.apple.com -> Anmeldung und Sicherheit -> App-spezifische Passwörter',
        'email_prompt': '📧 iCloud E-Mail: ',
        'password_prompt': '🔑 App-spezifisches Passwort (xxxx-xxxx-xxxx-xxxx): ',
        'email_empty': '❌ E-Mail darf nicht leer sein',
        'password_empty': '❌ Passwort darf nicht leer sein',
        'invalid_email': '❌ Ungültiges E-Mail-Format',
        'continue_anyway': 'Trotzdem fortfahren? (j/n): ',
        'password_unusual': '⚠️  Passwortformat sieht ungewöhnlich aus',
        'are_you_sure': 'Sind Sie sicher, dass dies korrekt ist? (j/n): ',
        'setup_cancelled': 'Einrichtung abgebrochen',
        'credentials_saved_keyring': '✅ Zugangsdaten sicher im Systemschlüsselbund gespeichert',
        'keyring_fallback': '⚠️  Konnte nicht auf Systemschlüsselbund zugreifen, verwende .env-Datei',
        'credentials_saved_file': '✅ Konfiguration sicher in {path} gespeichert',
        'ready_to_use': '🚀 Sie können jetzt iCalendar Sync verwenden!',
        
        # Calendar operations
        'available_calendars': '📅 Verfügbare Kalender ({count}):',
        'events_in_calendar': '📋 Ereignisse in \'{name}\' ({count} gefunden):',
        'event_created': '✅ Ereignis \'{summary}\' erfolgreich erstellt',
        'event_deleted': '🗑️  Ereignis erfolgreich gelöscht',
        
        # Errors
        'error_required_packages': '❌ Erforderliche Pakete nicht installiert: {error}',
        'error_run_install': 'Ausführen: pip install -r requirements.txt',
        'error_credentials_missing': '❌ iCloud-Zugangsdaten nicht konfiguriert',
        'error_auth_failed': '❌ Authentifizierung fehlgeschlagen: Ungültige Zugangsdaten',
        'error_network': '❌ Netzwerkfehler',
        'error_caldav': '❌ CalDAV-Fehler',
        'error_unexpected': '❌ Unerwarteter Fehler: {type}',
        'error_calendars_not_found': '❌ Kalender nicht gefunden',
        'error_calendar_not_found': '❌ Kalender \'{name}\' nicht gefunden',
        'error_events': '❌ Fehler beim Abrufen von Ereignissen',
        'error_listing_calendars': '❌ Fehler beim Auflisten der Kalender',
        'error_invalid_calendar_name': '❌ Ungültiger Kalendername',
        'error_days_range': '❌ days_ahead muss zwischen {min} und {max} liegen',
        'error_missing_fields': '❌ Fehlende Pflichtfelder: {fields}',
        'error_dtstart_type': '❌ dtstart muss ein datetime-Objekt sein',
        'error_dtend_type': '❌ dtend muss ein datetime-Objekt sein',
        'error_time_range': '❌ Endzeit des Ereignisses muss nach der Startzeit liegen',
        'error_creating_event': '❌ Fehler beim Erstellen des Ereignisses',
        'error_event_not_found': '❌ Ereignis oder Kalender nicht gefunden',
        'error_deleting_event': '❌ Fehler beim Löschen des Ereignisses',
        'error_invalid_uid': '❌ Gültige Ereignis-UID erforderlich',
        'error_uid_too_long': '❌ Ungültige Ereignis-UID (zu lang)',
        'error_calendar_required': '❌ Kalendername erforderlich',
        'error_json_required': '❌ Kalender und JSON-Daten erforderlich',
        'error_json_read': '❌ JSON-Datei konnte nicht gelesen werden',
        'error_json_too_large': '❌ JSON-Daten zu groß',
        'error_invalid_json': '❌ Ungültiges JSON: {error}',
        'error_invalid_datetime': '❌ Ungültiges Datums-/Uhrzeitformat: {error}',
        'error_uid_required': '❌ Kalender und Ereignis-UID erforderlich',
        
        # Warnings
        'warning_conflicts': '⚠️  Warnung: {count} konfliktierendes/s Ereignis/se gefunden:',
        'warning_conflict_item': '   - {summary} ({start} bis {end})',
        'confirm_continue': 'Trotzdem fortfahren? (j/n): ',
        'creation_cancelled': 'Ereigniserstellung abgebrochen',
        
        # Info
        'input_timeout': '⏱️  Eingabe-Timeout',
        'using_cached_connection': 'Verwende zwischengespeicherte CalDAV-Verbindung',
        'connection_successful': 'Erfolgreich mit iCloud CalDAV verbunden',
        'found_calendar': 'Kalender gefunden: {name}',
        'found_event': 'Ereignis gefunden: {summary}',
        'loaded_from_keyring': 'Passwort aus Schlüsselbund geladen',
    },
    
    'it': {
        # Setup
        'setup_title': '🔧 Configurazione di iCalendar Sync',
        'setup_intro': 'Per utilizzare iCalendar Sync, devi configurare le tue credenziali iCloud.',
        'setup_warning': '⚠️  Usa una Password specifica per l\'app, NON la tua password normale di Apple ID.',
        'setup_url': 'Ottienila da: https://appleid.apple.com -> Accesso e sicurezza -> Password specifiche per le app',
        'email_prompt': '📧 Email iCloud: ',
        'password_prompt': '🔑 Password specifica per l\'app (xxxx-xxxx-xxxx-xxxx): ',
        'email_empty': '❌ L\'email non può essere vuota',
        'password_empty': '❌ La password non può essere vuota',
        'invalid_email': '❌ Formato email non valido',
        'continue_anyway': 'Continuare comunque? (s/n): ',
        'password_unusual': '⚠️  Il formato della password sembra insolito',
        'are_you_sure': 'Sei sicuro che sia corretto? (s/n): ',
        'setup_cancelled': 'Configurazione annullata',
        'credentials_saved_keyring': '✅ Credenziali salvate in modo sicuro nel portachiavi di sistema',
        'keyring_fallback': '⚠️  Impossibile accedere al portachiavi di sistema, utilizzo del file .env',
        'credentials_saved_file': '✅ Configurazione salvata in modo sicuro in {path}',
        'ready_to_use': '🚀 Ora puoi usare iCalendar Sync!',
        
        # Calendar operations
        'available_calendars': '📅 Calendari Disponibili ({count}):',
        'events_in_calendar': '📋 Eventi in \'{name}\' ({count} trovati):',
        'event_created': '✅ Evento \'{summary}\' creato con successo',
        'event_deleted': '🗑️  Evento eliminato con successo',
        
        # Errors
        'error_required_packages': '❌ Pacchetti richiesti non installati: {error}',
        'error_run_install': 'Esegui: pip install -r requirements.txt',
        'error_credentials_missing': '❌ Credenziali iCloud non configurate',
        'error_auth_failed': '❌ Autenticazione fallita: Credenziali non valide',
        'error_network': '❌ Errore di rete',
        'error_caldav': '❌ Errore CalDAV',
        'error_unexpected': '❌ Errore imprevisto: {type}',
        'error_calendars_not_found': '❌ Calendari non trovati',
        'error_calendar_not_found': '❌ Calendario \'{name}\' non trovato',
        'error_events': '❌ Errore nel recupero degli eventi',
        'error_listing_calendars': '❌ Errore nell\'elencare i calendari',
        'error_invalid_calendar_name': '❌ Nome calendario non valido',
        'error_days_range': '❌ days_ahead deve essere tra {min} e {max}',
        'error_missing_fields': '❌ Campi richiesti mancanti: {fields}',
        'error_dtstart_type': '❌ dtstart deve essere un oggetto datetime',
        'error_dtend_type': '❌ dtend deve essere un oggetto datetime',
        'error_time_range': '❌ L\'ora di fine dell\'evento deve essere dopo l\'ora di inizio',
        'error_creating_event': '❌ Errore nella creazione dell\'evento',
        'error_event_not_found': '❌ Evento o calendario non trovato',
        'error_deleting_event': '❌ Errore nell\'eliminazione dell\'evento',
        'error_invalid_uid': '❌ UID evento valido richiesto',
        'error_uid_too_long': '❌ UID evento non valido (troppo lungo)',
        'error_calendar_required': '❌ Nome calendario richiesto',
        'error_json_required': '❌ Calendario e dati JSON richiesti',
        'error_json_read': '❌ Impossibile leggere il file JSON',
        'error_json_too_large': '❌ Dati JSON troppo grandi',
        'error_invalid_json': '❌ JSON non valido: {error}',
        'error_invalid_datetime': '❌ Formato data/ora non valido: {error}',
        'error_uid_required': '❌ Calendario e UID evento richiesti',
        
        # Warnings
        'warning_conflicts': '⚠️  Attenzione: {count} evento/i in conflitto trovato/i:',
        'warning_conflict_item': '   - {summary} ({start} a {end})',
        'confirm_continue': 'Continuare comunque? (s/n): ',
        'creation_cancelled': 'Creazione evento annullata',
        
        # Info
        'input_timeout': '⏱️  Timeout input',
        'using_cached_connection': 'Utilizzo connessione CalDAV in cache',
        'connection_successful': 'Connesso con successo a iCloud CalDAV',
        'found_calendar': 'Calendario trovato: {name}',
        'found_event': 'Evento trovato: {summary}',
        'loaded_from_keyring': 'Password caricata dal portachiavi',
    },
}


def get_language() -> str:
    """
    Detect system language or use environment variable
    Priority: ICALENDAR_LANG > system locale > English
    """
    # Check environment variable first
    env_lang = os.getenv('ICALENDAR_LANG', '').lower()
    if env_lang in SUPPORTED_LANGUAGES:
        return env_lang
    
    # Try to detect from system locale
    try:
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            lang_code = system_locale.split('_')[0].lower()
            if lang_code in SUPPORTED_LANGUAGES:
                return lang_code
    except Exception:
        pass
    
    # Default to English
    return 'en'


# Global language setting
CURRENT_LANGUAGE = get_language()


def _(key: str, **kwargs) -> str:
    """
    Get translated string for current language
    
    Args:
        key: Translation key
        **kwargs: Format parameters
    
    Returns:
        Translated and formatted string
    """
    translations = TRANSLATIONS.get(CURRENT_LANGUAGE, TRANSLATIONS['en'])
    text = translations.get(key, TRANSLATIONS['en'].get(key, key))
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    
    return text


def set_language(lang: str) -> bool:
    """
    Set language manually
    
    Args:
        lang: Language code (en, es, fr, de, it)
    
    Returns:
        True if language was set, False if invalid
    """
    global CURRENT_LANGUAGE
    
    lang = lang.lower()
    if lang in SUPPORTED_LANGUAGES:
        CURRENT_LANGUAGE = lang
        return True
    
    return False


def get_supported_languages() -> list:
    """Get list of supported language codes"""
    return SUPPORTED_LANGUAGES.copy()
