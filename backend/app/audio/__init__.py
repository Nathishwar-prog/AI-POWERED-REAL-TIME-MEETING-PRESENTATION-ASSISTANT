"""Audio + transcription abstraction.

The pipeline consumes an async stream of :class:`~app.models.TranscriptChunk`
objects and does not care where they come from.  This package provides that
stream from a scripted text file (:mod:`~app.audio.mock_transcriber`) or from a
real audio file via faster-whisper (:mod:`~app.audio.whisper_transcriber` +
:mod:`~app.audio.file_source`).  A future Zoom source implements the same
:class:`~app.audio.base.AudioSource` interface - see
:mod:`~app.audio.zoom_source`.
"""
