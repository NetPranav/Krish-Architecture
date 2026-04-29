/**
 * Platform-Aware Translation Engine
 * 
 * Detects if the app is running on the web or natively (iOS/Android).
 * - Web: Uses Google Translate widget injected dynamically.
 * - Native: Uses offline ML Kit translation to walk and mutate the DOM.
 */

/**
 * Main entry point to change the app language.
 * Routes to the correct strategy based on platform.
 * 
 * @param {string} targetLangCode - The 2-letter language code (e.g., 'hi', 'mr', 'en')
 */
export async function changeAppLanguage(targetLangCode) {
  let platform = 'web';
  try {
    const { Capacitor } = await import('@capacitor/core');
    platform = Capacitor.getPlatform();
  } catch (e) {
    console.warn("Capacitor not found, defaulting to web strategy.");
  }

  if (platform === 'web') {
    await applyWebTranslation(targetLangCode);
  } else if (platform === 'ios' || platform === 'android') {
    await applyNativeTranslation(targetLangCode);
  } else {
    console.warn(`Unsupported platform for translation: ${platform}`);
  }
}

/**
 * Web Strategy: Google Translate Injection
 * Dynamically creates the widget and triggers translation to the targetLangCode.
 * Hides the annoying banner via CSS.
 * 
 * @param {string} targetLangCode 
 */
async function applyWebTranslation(targetLangCode) {
  // 1. If the Google Translate widget is already loaded, we can just trigger a change event
  const select = document.querySelector('.goog-te-combo');
  if (select) {
    select.value = targetLangCode === 'en' ? '' : targetLangCode;
    select.dispatchEvent(new Event('change'));
    return;
  }

  // 2. If it's not loaded, we set the cookie so it automatically translates on init
  if (targetLangCode === 'en') {
    document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; domain=" + location.hostname + "; path=/;";
  } else {
    const cookieVal = `/en/${targetLangCode}`;
    document.cookie = `googtrans=${cookieVal}; path=/`;
    document.cookie = `googtrans=${cookieVal}; domain=${location.hostname}; path=/`;
  }

  // Prevent multiple script injections
  if (document.getElementById('google_translate_element')) {
    return;
  }

  // 3. Create a hidden div for the Google Translate element
  const gtDiv = document.createElement('div');
  gtDiv.id = 'google_translate_element';
  gtDiv.style.display = 'none';
  document.body.appendChild(gtDiv);

  // 4. Set up the initialization callback
  window.googleTranslateElementInit = function () {
    new window.google.translate.TranslateElement({
      pageLanguage: 'en',
      autoDisplay: false
    }, 'google_translate_element');
  };

  // 5. Inject the Google Translate script
  const script = document.createElement('script');
  script.src = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
  script.async = true;
  document.head.appendChild(script);

  // 6. Inject CSS to hide the ugly top banner and fix body positioning
  const style = document.createElement('style');
  style.innerHTML = `
    /* Hide the top translation banner */
    .skiptranslate iframe {
      display: none !important;
    }
    /* Fix body pushing down */
    body {
      top: 0px !important;
    }
    /* Hide tooltip popups */
    #goog-gt-tt {
      display: none !important;
    }
    /* Hide Google translate widget */
    .goog-te-banner-frame {
      display: none !important;
    }
  `;
  document.head.appendChild(style);
}

/**
 * Native Strategy: Offline ML Kit + DOM Mutator
 * Downloads required language models and translates visible text nodes offline.
 * 
 * @param {string} targetLangCode - The target language code to translate into
 */
async function applyNativeTranslation(targetLangCode) {
  try {
    const { Translation } = await import('@capacitor-mlkit/translation');
    // 1. Model Management: Check if model is downloaded
    // Fallback to empty array if downloadedModels is undefined
    const { downloadedModels = [] } = await Translation.getDownloadedModels();
    
    if (!downloadedModels.includes(targetLangCode)) {
      console.log(`Downloading ML Kit model for ${targetLangCode}...`);
      await Translation.downloadModel({ language: targetLangCode });
      console.log(`Model for ${targetLangCode} downloaded successfully.`);
    }

    // 2. The DOM Walker: Find all visible text nodes
    // Using NodeFilter.SHOW_TEXT to isolate text nodes
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(node) {
          // Ignore empty whitespace nodes
          if (node.nodeValue.trim() === '') {
            return NodeFilter.FILTER_REJECT;
          }
          // Ignore script, style, and noscript tags
          const parentTag = node.parentNode.tagName;
          if (parentTag === 'SCRIPT' || parentTag === 'STYLE' || parentTag === 'NOSCRIPT') {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      },
      false
    );

    // Extract all acceptable text nodes into an array first
    const nodesToTranslate = [];
    let currentNode;
    while ((currentNode = walker.nextNode())) {
      nodesToTranslate.push(currentNode);
    }

    // 3. Translate and Mutate DOM
    for (const node of nodesToTranslate) {
      const originalText = node.nodeValue;
      const trimmedText = originalText.trim();
      
      // We only translate if there is meaningful text
      if (trimmedText) {
        try {
          const result = await Translation.translate({
            text: trimmedText,
            sourceLanguage: 'en',
            targetLanguage: targetLangCode
          });
          
          // Replace the original text node's value with the translated text,
          // preserving any leading/trailing whitespace.
          node.nodeValue = originalText.replace(trimmedText, result);
        } catch (err) {
          console.error(`Failed to translate text: "${trimmedText}"`, err);
        }
      }
    }
  } catch (error) {
    console.error('Error applying native translation:', error);
  }
}
