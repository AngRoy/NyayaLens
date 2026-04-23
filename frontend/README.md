# NyayaLens — frontend

Flutter web client. Run with:

```sh
flutter pub get
flutter run -d chrome
```

Requires Flutter 3.24+ and Dart 3.5+.

The `android/`, `ios/`, `linux/`, `macos/`, `windows/` platform folders are
intentionally not committed — they are regenerated locally when a contributor
needs to build for that platform. This keeps the repo web-first.

After cloning, run:

```sh
flutter create --platforms=web .     # regenerates any missing web scaffold
flutter pub get
```
