import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.smartagri.app',
  appName: 'SmartAgri',
  webDir: 'out',
  // Removed server configuration so the app loads the bundled 'out' folder locally offline!
};

export default config;
