# Browser Support Quick Reference

## TL;DR

✅ **Full Support:** Chrome 88+, Safari 15+, Firefox 103+, Edge 88+  
⚠️ **Partial Support:** Safari 13-14, Firefox 75-102, older Chrome/Edge  
❌ **Degraded Experience:** IE 11, very old browsers

---

## Quick Feature Check

Open browser console and run:

```javascript
const features = {
  backdropFilter: CSS.supports('backdrop-filter', 'blur(10px)'),
  clamp: CSS.supports('font-size', 'clamp(1rem, 2vw, 2rem)'),
  customProperties: CSS.supports('--test', '0'),
  backgroundClip: CSS.supports('background-clip', 'text'),
  aspectRatio: CSS.supports('aspect-ratio', '16 / 9'),
  gap: CSS.supports('gap', '1rem')
};

console.table(features);
```

---

## Browser Minimum Versions

| Browser | Minimum Version | Recommended |
|---------|----------------|-------------|
| Chrome | 76 | 88+ |
| Safari | 9 | 15+ |
| Firefox | 75 | 103+ |
| Edge | 79 | 88+ |
| iOS Safari | 13 | 15+ |
| Chrome Mobile | 76 | Latest |

---

## What Works Where

### ✅ Works Everywhere (with fallbacks)
- Basic layout and functionality
- Text content and navigation
- Forms and buttons
- Responsive design
- Accessibility features

### ⚠️ Modern Browsers Only
- Glassmorphism (backdrop-filter)
- Neon glow animations
- Gradient text effects
- Advanced CSS animations
- clamp() responsive typography

### ❌ Not Supported (IE 11)
- CSS custom properties
- backdrop-filter
- clamp()
- aspect-ratio
- gap property
- Complex animations

---

## Quick Fallback Reference

### Glassmorphism → Solid Background
```css
/* Modern */
background: rgba(42, 42, 42, 0.6);
backdrop-filter: blur(20px);

/* Fallback */
background: rgba(42, 42, 42, 0.95);
```

### Gradient Text → Solid Color
```css
/* Modern */
background: linear-gradient(135deg, #8B5CF6, #06B6D4);
background-clip: text;
color: transparent;

/* Fallback */
color: #8B5CF6;
```

### clamp() → Media Queries
```css
/* Modern */
font-size: clamp(1rem, 2vw, 2rem);

/* Fallback */
font-size: 1rem;
@media (min-width: 768px) {
  font-size: 1.5rem;
}
@media (min-width: 1024px) {
  font-size: 2rem;
}
```

### Animations → Static Effects
```css
/* Modern */
animation: neonPulse 3s infinite;

/* Fallback */
box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
```

---

## Testing Checklist

### Before Deployment
- [ ] Test in Chrome (latest)
- [ ] Test in Safari (latest)
- [ ] Test in Firefox (latest)
- [ ] Test in Edge (latest)
- [ ] Test on iPhone (iOS Safari)
- [ ] Test on Android (Chrome Mobile)
- [ ] Run Lighthouse audit (90+ score)
- [ ] Check accessibility (WCAG AA)
- [ ] Verify reduced motion works
- [ ] Test keyboard navigation

### Performance Targets
- [ ] FPS: 55-60 on desktop
- [ ] FPS: 50+ on mobile
- [ ] Lighthouse Performance: 90+
- [ ] First Contentful Paint: < 1.5s
- [ ] Time to Interactive: < 3.5s

---

## Common Issues

### Issue: Blurry text on Safari
**Fix:** Add `-webkit-font-smoothing: antialiased`

### Issue: Animations stuttering
**Fix:** Add `will-change: transform` and `transform: translateZ(0)`

### Issue: Layout shift on load
**Fix:** Add `contain: layout style paint` to animated elements

### Issue: Touch targets too small
**Fix:** Ensure min-height and min-width of 44px

---

## Browser-Specific Notes

### Safari
- Requires `-webkit-` prefix for backdrop-filter
- Requires `-webkit-` prefix for background-clip: text
- May have different blur rendering

### Firefox
- backdrop-filter only in v103+
- May need adjusted opacity for glass effects

### Chrome/Edge
- Best performance with will-change
- Full support for all features

### IE 11
- Use hard-coded colors (no CSS variables)
- Solid backgrounds (no glassmorphism)
- Static effects (no complex animations)

---

## Quick Test Page

Open: `.kiro/specs/homepage-redesign/browser-test.html`

Shows:
- Which features are supported
- Which fallbacks are active
- Browser information
- Real-time feature detection

---

## Support Policy

**Full Support:**
- Last 2 versions of major browsers
- Modern mobile browsers

**Graceful Degradation:**
- Older browsers with fallbacks
- Functional but less visual

**No Support:**
- IE 10 and below
- Very old mobile browsers

---

## Need Help?

1. Check `CROSS_BROWSER_TESTING_REPORT.md` for detailed info
2. Check `BROWSER_TESTING_GUIDE.md` for testing procedures
3. Use `browser-test.html` for feature detection
4. Check MDN Web Docs for feature support
5. Use Can I Use (caniuse.com) for compatibility

---

## Quick Commands

### Build for production
```bash
cd frontend
npm run build
```

### Test locally
```bash
cd frontend
npm start
```

### Run Lighthouse
```bash
# Chrome DevTools > Lighthouse > Generate Report
```

### Check bundle size
```bash
cd frontend
npm run build
ls -lh build/static/css/
ls -lh build/static/js/
```

---

## Performance Tips

1. **Use will-change sparingly** - Only on elements that will animate
2. **Avoid animating expensive properties** - Stick to transform and opacity
3. **Use transform: translateZ(0)** - Forces GPU acceleration
4. **Reduce blur on mobile** - Use lower blur values for better performance
5. **Test on real devices** - Emulators don't show real performance

---

## Accessibility Reminders

- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] Reduced motion preference respected
- [ ] Screen reader labels present
- [ ] Touch targets 44px minimum

---

## Last Updated

January 9, 2025

---

## Quick Links

- [MDN @supports](https://developer.mozilla.org/en-US/docs/Web/CSS/@supports)
- [Can I Use](https://caniuse.com/)
- [Web.dev](https://web.dev/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
