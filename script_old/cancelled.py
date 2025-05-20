#src/cancelled.py

from visualization import plot_cancellation_reasons

def main():
    cancellation_file = '../reports/canceled_tickets.txt'
    
    # Generate the cancellation reasons bar chart
    plot_cancellation_reasons(cancellation_file)

if __name__ == '__main__':
    main()
