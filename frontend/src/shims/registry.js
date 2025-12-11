
// Shim for react-native-web/dist/apis/StyleSheet/registry
// This is needed because react-bits uses an old internal API that was removed in newer react-native-web versions.
import { StyleSheet } from 'react-native-web';

const registry = {
  resolve: (style) => {
    // Minimal implementation: just return the style as-is.
    // Real registry would return { className, style } etc.
    // This allows the app to build, though some specific react-bits optimizations might be skipped.
    const flattened = StyleSheet.flatten(style);
    return { style: flattened, classList: [] };
  }
};

export default registry;
