import 'package:nyayalens_client/shared/platform/url_opener_stub.dart'
    if (dart.library.html)
        'package:nyayalens_client/shared/platform/url_opener_web.dart';

void openExternalUrl(String url) => openExternalUrlImpl(url);
