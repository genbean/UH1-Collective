#ifndef VERSION_H
#define VERSION_H

// HeliSR Configurator's own version (forked from FreeJoyConfiguratorQt 1.7.3b0)
#define MAJOR_VERSION 1
#define MINOR_VERSION 0
#define PATCH_VERSION 0

#define PROJECT_URL "https://github.com/genbean/UH1-Collective"
#define PROJECT_DOCS_URL PROJECT_URL "/tree/main/Software"

#ifdef INNO_SETUP
	#define APP_VERSION Str(MAJOR_VERSION) + "." + Str(MINOR_VERSION) + "." + Str(PATCH_VERSION)
#else
	#define str(s) #s
	#define xstr(s) str(s)
	#define APP_VERSION xstr(MAJOR_VERSION) "." xstr(MINOR_VERSION) "." xstr(PATCH_VERSION)
#endif

#endif // VERSION_H
