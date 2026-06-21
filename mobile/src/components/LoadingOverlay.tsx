import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, spacing } from '../theme';

interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message = '正在处理中...' }: LoadingOverlayProps) {
  return (
    <View style={styles.overlay}>
      <View style={styles.box}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.text}>{message}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  box: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: spacing.xl,
    alignItems: 'center',
    minWidth: 200,
  },
  text: {
    marginTop: spacing.md,
    fontSize: fontSize.md,
    color: colors.text,
    textAlign: 'center',
  },
});
