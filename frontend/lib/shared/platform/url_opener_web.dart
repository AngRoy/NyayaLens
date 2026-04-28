import 'package:web/web.dart' as web;

void openExternalUrlImpl(String url) {
  web.window.open(url, '_blank', 'noopener,noreferrer');
}
