import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.smartagri.app',
  appName: 'SmartAgri',
  webDir: 'out',
  server: {
    url: 'http://192.168.137.198:3000',
    cleartext: true
  }
};

export default config;
