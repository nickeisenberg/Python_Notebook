import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from math import ceil, floor
import scipy.signal as sps
from sklearn.preprocessing import MinMaxScaler

stock_info = yf.Ticker('GME')

price_history = stock_info.history(period='2y',
                                 interval='1d',
                                 actions=False)

price_history['Open'].to_csv('/Users/nickeisenberg/GitRepos/Python_Misc/Misc/Plots/gme_open.csv')
open_price = price_history['Open'].values

# Min/Max scaler
max_open = np.max(open_price)
min_open = np.min(open_price)
open_price -= min_open
open_price /= (max_open - min_open)

# Wiener filtered data
open_price_wiener = sps.wiener(open_price, 9)

# median filtered data
open_price_med = sps.medfilt(open_price, 9)

'''
#-Plotting-a-spectrogram---------------------------
time_window = 256
time_step = 256
time_unit = 1

spectrogram = []
spec_times = []
freqs = np.fft.rfftfreq(time_window, d=time_unit)

for time_start in np.arange(0, len(open_price), time_step):

    data_time_ref = time_start + time_step / 2
    data = open_price[time_start : time_start + time_step]

    if len(data) < time_window:
        continue

    spec_times.append(data_time_ref)
    spectrogram.append(np.abs(np.fft.rfft(data)))

spectrogram = np.array(spectrogram).T
spec_times = np.array(spec_times)

fig, ax = plt.subplots()
x2d, y2d = np.meshgrid(spec_times, freqs)
pc = ax.pcolormesh(spec_times, freqs, 10 * np.log10(spectrogram + .001), shading='auto')
fig.colorbar(pc)
plt.show()
#--------------------------------------------------
'''

'''
#-Combined-frequency-profile-----------------------
time_window = 64
time_step = 64
time_unit = 1

spectrogram = []
spec_times = []
freqs = np.fft.rfftfreq(time_window, d=time_unit)

for time_start in np.arange(0, len(open_price), time_step):

    data_time_ref = time_start + time_step / 2
    data = open_price[time_start : time_start + time_step]

    if len(data) < time_window:
        continue

    spec_times.append(data_time_ref)
    spectrogram.append(np.abs(np.fft.rfft(data)))

spectrogram = np.array(spectrogram)
spectrogram = np.percentile(spectrogram, 90,  axis=0)
spec_times = np.array(spec_times)

plt.subplot(133)
plt.plot(freqs, spectrogram)
#--------------------------------------------------
'''

#-Finding-peaks-and-bandwidths-for-butter-filters--
time = np.linspace(0, 2, len(open_price))
freq = np.fft.rfftfreq(len(open_price), d = time[1] - time[0])
fft = abs(np.fft.rfft(open_price))

peak_idx, _ = sps.find_peaks(fft)
peak_pairs = []
for pi in peak_idx:
    peak_pairs.append([freq[pi], fft[pi]])
peak_pairs = np.array(peak_pairs)

prom = sps.peak_prominences(fft, peak_idx)
widths = sps.peak_widths(fft, peak_idx, rel_height=.5)
peak_array = []
for pi, pp, pw, pf, pv in zip(peak_idx, prom[0], widths[0], peak_pairs[:,0], peak_pairs[:,1]):
    peak_array.append([pi, pp, pw, pf, pv])
peak_array = np.array(peak_array)
peak_array = peak_array[peak_array[:,1].argsort()[::-1]]

worthy_peaks = peak_array[:5]
worthy_peaks = worthy_peaks[worthy_peaks[:,0].argsort()]

#-Various-butter-filters---------------------------
#-Lowpass-----------------
# sos_l = sps.butter(9, 25, 'lowpass', fs=len(open_price), output='sos')
# filt_data_l = sps.sosfiltfilt(sos_l, open_price)

#-Bandpass----------------
# The lowpass with cutoff 20 removed the signal with freq=17. Not sure why.
# We can use bandpass filters to look at each of the above mentioned frequencies.

filt_data_bp = []
implied_noise_bp = []
for wp in worthy_peaks:
    wpi, wpp, wpw, wpf, wpv = wp
    lowcut, highcut = wpf - (wpw / 2), wpf + (wpw / 2)
    sos = sps.butter(9, [lowcut, highcut], 'bandpass', fs=len(open_price), output='sos')
    filt_data = sps.sosfiltfilt(sos, open_price)
    max_bp, min_bp = np.max(filt_data), np.min(filt_data)
    filt_data -= min_bp
    filt_data /= (max_bp - min_bp)
    implied_noise = open_price - filt_data
    filt_data_bp.append(filt_data)
    implied_noise_bp.append(implied_noise)
filt_data_bp = np.array(filt_data_bp)
implied_noise_bp.append(implied_noise_bp)

# plt.subplot(231)
# plt.plot(time, open_price)
# plt.title('gme open price: 1hr int')
# for i in range(len(filt_data_bp)):
#     plt.subplot(2,3,i+2)
#     plt.plot(time, filt_data_bp[i])
#     plt.title(f'BP for freq: {worthy_peaks[i][3]}')
# 
# plt.show()

combined_freqs = np.sum(filt_data_bp, axis=0)
max_comb, min_comb = np.max(combined_freqs), np.min(combined_freqs)
combined_freqs -= min_comb
combined_freqs /= (max_comb - min_comb)
comb_noise = open_price - combined_freqs
plt.subplot(121)
plt.plot(time, open_price, label='gme open')
plt.plot(time, combined_freqs, label='combined worth freqs')
plt.legend(loc='upper right')
plt.subplot(122)
plt.plot(time, comb_noise, label='combined implied noise')
plt.plot(time, combined_freqs, label='combined worth freqs')
plt.legend(loc='upper right')
plt.show()
#--------------------------------------------------

